"""Importadores de planilhas, Google Sheets e CSV."""

import csv
from pathlib import Path
import unicodedata

from backend.database import get_conn
from backend.models import get_config
from backend.services.status_service import emitir_advertencias_falta

_ALIASES_PARTICIPANTES = {
    "nome": ("nome",),
    "matricula": ("matricula", "matrícula"),
    "email": ("email", "e-mail"),
    "telefone": ("telefone", "celular", "whatsapp"),
    "turno": ("turno",),
    "curso": ("curso",),
    "instituicao": ("institui", "universidade", "faculdade"),
    "cidade": ("cidade", "grande bh", "bh"),
    "bolsista": ("bolsista", "prouni", "pro-uni"),
    "trabalha": ("trabalha", "trabalho", "emprego"),
    "idade": ("idade",),
    "periodo": ("periodo", "período", "semestre cursando"),
    "passou_algoritmos": ("algoritmo", "aeds", "introducao", "introdução", "intro a alg"),
    "primeiro_periodo": ("primeiro periodo", "1o periodo", "1º periodo", "primeiro per"),
}


def _norm(texto):
    """Remove acentos e normaliza texto para comparação de cabeçalhos e nomes."""
    nfkd = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _resolver_credentials_path():
    raiz = Path(__file__).resolve().parents[2] / "credentials.json"
    if raiz.exists():
        return raiz
    return Path(__file__).parent / "credentials.json"


def _abrir_planilha(url):
    """Abre a primeira aba de uma planilha do Google Sheets usando a conta de serviço."""
    import gspread

    gc = gspread.service_account(filename=str(_resolver_credentials_path()))
    return gc.open_by_url(url).sheet1


def _find_idx(headers_norm, *keywords):
    for i, header in enumerate(headers_norm):
        if any(kw in header for kw in keywords):
            return i
    return None


def _mapear_colunas(headers, campos):
    """Mapeia nomes lógicos de campo para o nome original da coluna na planilha."""
    keys_norm = {_norm(k): k for k in headers}
    mapeamento = {}
    for campo in campos:
        aliases = _ALIASES_PARTICIPANTES[campo]
        mapeamento[campo] = next(
            (original for norm_key, original in keys_norm.items() if any(kw in norm_key for kw in aliases)),
            None,
        )
    return mapeamento


def _get_col(record, cols, campo):
    col = cols.get(campo)
    return str(record.get(col, "") or "").strip() if col else ""


def _parse_sim_nao(texto, keywords=("sim",), nullable=False):
    raw = _norm(texto)
    if not raw and nullable:
        return None
    return 1 if any(kw in raw for kw in keywords) else 0


def _elegivel_programa(record, cols):
    curso = _norm(_get_col(record, cols, "curso"))
    inst = _norm(_get_col(record, cols, "instituicao"))
    return "engenharia de software" in curso and "puc" in inst


def _extrair_perfil_comum(record, cols):
    idade_s = _get_col(record, cols, "idade")
    return {
        "nome": _get_col(record, cols, "nome"),
        "telefone": _get_col(record, cols, "telefone") or None,
        "turno": _get_col(record, cols, "turno") or None,
        "idade": int(idade_s) if idade_s.isdigit() else None,
        "cidade_bh": _parse_sim_nao(_get_col(record, cols, "cidade"), ("sim", "grande bh", "bh")),
        "bolsista": _parse_sim_nao(_get_col(record, cols, "bolsista")),
        "trabalha": _parse_sim_nao(_get_col(record, cols, "trabalha")),
    }


def sincronizar_presencas_sheets(reuniao_id):
    url = get_config("sheets_presenca_url")
    if not url:
        raise ValueError("URL da planilha não configurada. Vá em Configurações → Google Forms.")

    records = _abrir_planilha(url).get_all_records()

    conn = get_conn()
    padrinhos = conn.execute(
        "SELECT id, nome, matricula, email FROM padrinhos WHERE ativo=1"
    ).fetchall()

    por_matricula = {str(p["matricula"] or "").strip(): p["id"] for p in padrinhos if p["matricula"]}
    por_email = {(p["email"] or "").lower().strip(): p["id"] for p in padrinhos if p["email"]}
    por_nome = {_norm(p["nome"]): p["id"] for p in padrinhos}

    registradas = 0
    nao_reconhecidas = []

    for record in records:
        keys = {_norm(k): str(v).strip() for k, v in record.items()}

        def _campo(*kws):
            return next((str(v).strip() for k, v in keys.items() if any(kw in k for kw in kws)), "")

        matricula = _campo("matricula")
        email = _campo("email", "mail").lower()
        nome = _campo("nome")

        padrinho_id = (
            por_matricula.get(matricula)
            or por_email.get(email)
            or por_nome.get(_norm(nome))
        )

        if padrinho_id:
            conn.execute("""
                INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
                VALUES (?, ?, 1, 0)
                ON CONFLICT(reuniao_id, padrinho_id) DO UPDATE SET presente=1
            """, (reuniao_id, padrinho_id))
            registradas += 1
        else:
            identificador = matricula or email or nome or "?"
            nao_reconhecidas.append(f"{nome} {identificador}".strip())

    conn.commit()
    conn.close()
    return {"registradas": registradas, "nao_reconhecidas": nao_reconhecidas}


def sincronizar_responsaveis_temas():
    url = get_config("sheets_inscricoes_url")
    if not url:
        raise ValueError("URL da planilha de inscrições não configurada. Cole o link em Temas.")

    rows = _abrir_planilha(url).get_all_values()
    if len(rows) < 2:
        return {"atualizados": 0, "nao_reconhecidos": []}

    conn = get_conn()
    padrinhos = conn.execute("SELECT id, nome, matricula FROM padrinhos WHERE ativo=1").fetchall()
    por_nome = {_norm(p["nome"]): p["id"] for p in padrinhos}
    por_matricula = {str(p["matricula"] or "").strip(): p["id"] for p in padrinhos if p["matricula"]}
    temas_por_titulo = {_norm(t["titulo"]): t["id"] for t in conn.execute("SELECT id, titulo FROM temas").fetchall()}

    atualizados = 0
    nao_reconhecidos = []
    header_norm = [_norm(h) for h in rows[0]]
    is_forms = any(kw in header_norm[0] for kw in ("carimbo", "timestamp", "data/hora", "hora"))

    if is_forms:
        idx_nome = _find_idx(header_norm, "nome")
        idx_matricula = _find_idx(header_norm, "matricula")
        idx_tema = _find_idx(header_norm, "tema", "apresentar", "inscri", "qual")

        if idx_tema is None:
            conn.close()
            raise ValueError("Coluna de tema não encontrada na planilha de respostas.")

        tema_padrinhos_novos = {}
        for row in rows[1:]:
            if not row or len(row) <= idx_tema:
                continue
            tema_id = temas_por_titulo.get(_norm(row[idx_tema].strip()))
            if not tema_id:
                continue

            pid = None
            if idx_matricula is not None and idx_matricula < len(row):
                pid = por_matricula.get(str(row[idx_matricula]).strip())
            if pid is None and idx_nome is not None and idx_nome < len(row):
                pid = por_nome.get(_norm(row[idx_nome].strip()))

            if pid:
                lista = tema_padrinhos_novos.setdefault(tema_id, [])
                if pid not in lista:
                    lista.append(pid)
                atualizados += 1
            else:
                nome_str = row[idx_nome].strip() if idx_nome is not None and idx_nome < len(row) else "?"
                if nome_str:
                    nao_reconhecidos.append(nome_str)

        for tema_id, pids in tema_padrinhos_novos.items():
            conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
            conn.executemany(
                "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
                [(tema_id, pid) for pid in pids],
            )
    else:
        for row in rows[1:]:
            if not row or not row[0].strip():
                continue
            tema_id = temas_por_titulo.get(_norm(row[0].strip()))
            if not tema_id:
                continue

            novos_ids = []
            for cell in row[1:]:
                val = cell.strip()
                if not val:
                    continue
                pid = por_matricula.get(val) or por_nome.get(_norm(val))
                if pid:
                    if pid not in novos_ids:
                        novos_ids.append(pid)
                    atualizados += 1
                else:
                    nao_reconhecidos.append(val)

            conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
            conn.executemany(
                "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
                [(tema_id, pid) for pid in novos_ids],
            )

    conn.commit()
    conn.close()
    return {"atualizados": atualizados, "nao_reconhecidos": list(dict.fromkeys(nao_reconhecidos))}


def importar_padrinhos_sheets(url):
    records = _abrir_planilha(url).get_all_records()
    if not records:
        return {"importados": 0, "ignorados": 0, "duplicatas": 0}

    cols = _mapear_colunas(
        records[0].keys(),
        ("nome", "matricula", "email", "telefone", "turno", "curso", "instituicao", "cidade", "bolsista", "trabalha", "idade", "periodo", "passou_algoritmos"),
    )

    conn = get_conn()
    existing = {
        str(p["matricula"]).strip(): True
        for p in conn.execute("SELECT matricula FROM padrinhos").fetchall()
        if p["matricula"]
    }

    importados = ignorados = duplicatas = 0
    for rec in records:
        if not _elegivel_programa(rec, cols):
            ignorados += 1
            continue

        matricula = _get_col(rec, cols, "matricula")
        if matricula and matricula in existing:
            duplicatas += 1
            continue

        perfil = _extrair_perfil_comum(rec, cols)
        if not perfil["nome"]:
            ignorados += 1
            continue

        conn.execute(
            """
            INSERT INTO padrinhos (nome, matricula, email, telefone, turno, idade, cidade_bh, bolsista, trabalha, periodo, passou_algoritmos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                perfil["nome"],
                matricula or None,
                _get_col(rec, cols, "email") or None,
                perfil["telefone"],
                perfil["turno"],
                perfil["idade"],
                perfil["cidade_bh"],
                perfil["bolsista"],
                perfil["trabalha"],
                _get_col(rec, cols, "periodo") or None,
                _parse_sim_nao(_get_col(rec, cols, "passou_algoritmos"), nullable=True),
            ),
        )
        if matricula:
            existing[matricula] = True
        importados += 1

    conn.commit()
    conn.close()
    return {"importados": importados, "ignorados": ignorados, "duplicatas": duplicatas}


def importar_calouros_sheets(url):
    records = _abrir_planilha(url).get_all_records()
    if not records:
        return {"importados": 0, "ignorados": 0, "duplicatas": 0}

    cols = _mapear_colunas(
        records[0].keys(),
        ("nome", "telefone", "turno", "curso", "instituicao", "cidade", "bolsista", "trabalha", "idade", "primeiro_periodo"),
    )

    conn = get_conn()
    existing_nomes = {_norm(c["nome"]): True for c in conn.execute("SELECT nome FROM calouros").fetchall()}

    importados = ignorados = duplicatas = 0
    for rec in records:
        perfil = _extrair_perfil_comum(rec, cols)
        if not _elegivel_programa(rec, cols) or not perfil["nome"]:
            ignorados += 1
            continue

        nome_norm = _norm(perfil["nome"])
        if nome_norm in existing_nomes:
            duplicatas += 1
            continue

        conn.execute(
            """
            INSERT INTO calouros (nome, telefone, turno, idade, cidade_bh, bolsista, trabalha, primeiro_periodo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                perfil["nome"],
                perfil["telefone"],
                perfil["turno"],
                perfil["idade"],
                perfil["cidade_bh"],
                perfil["bolsista"],
                perfil["trabalha"],
                _parse_sim_nao(_get_col(rec, cols, "primeiro_periodo"), nullable=True),
            ),
        )
        existing_nomes[nome_norm] = True
        importados += 1

    conn.commit()
    conn.close()
    return {"importados": importados, "ignorados": ignorados, "duplicatas": duplicatas}


def importar_presencas_csv(caminho_csv, reuniao_id):
    col_matricula = None
    col_situacao = None
    rows_data = []

    with open(caminho_csv, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [c.strip() for c in (reader.fieldnames or [])]
        for col in fieldnames:
            col_lower = col.lower()
            if "matrícula" in col_lower or "matricula" in col_lower:
                col_matricula = col
            if "situação" in col_lower or "situacao" in col_lower or "situac" in col_lower:
                col_situacao = col
        if not col_matricula:
            return {"erro": "Coluna de matrícula não encontrada no CSV."}
        for raw in reader:
            rows_data.append({k.strip(): v for k, v in raw.items()})

    conn = get_conn()
    processados = 0
    nao_encontrados = []

    todos_padrinhos = conn.execute("SELECT id, matricula FROM padrinhos WHERE ativo=1").fetchall()
    matricula_para_id = {p["matricula"]: p["id"] for p in todos_padrinhos}

    for row in rows_data:
        matricula = str(row.get(col_matricula, "")).strip().replace(".0", "")
        padrinho_id_val = matricula_para_id.get(matricula)

        if padrinho_id_val is None:
            nao_encontrados.append(matricula)
            continue

        presente = 1
        justificada = 0
        if col_situacao:
            situacao = str(row.get(col_situacao, "")).strip().lower()
            if "justificativa" in situacao or "ausente" in situacao:
                presente = 0
                justificada = 1

        conn.execute("""
            INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(reuniao_id, padrinho_id)
            DO UPDATE SET presente=excluded.presente, justificada=excluded.justificada
        """, (reuniao_id, padrinho_id_val, presente, justificada))
        processados += 1

    # Registra ausência para quem não apareceu no CSV e ainda não tem presença
    for p in todos_padrinhos:
        registro = conn.execute(
            "SELECT id FROM presencas WHERE reuniao_id=? AND padrinho_id=?",
            (reuniao_id, p["id"]),
        ).fetchone()
        if not registro:
            conn.execute(
                "INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada) VALUES (?, ?, 0, 0)",
                (reuniao_id, p["id"]),
            )

    conn.commit()
    emitir_advertencias_falta(reuniao_id)
    conn.close()
    return {"processados": processados, "nao_encontrados": nao_encontrados}
