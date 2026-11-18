"""Importadores de planilhas, Google Sheets e CSV."""

from database import get_conn
from models import get_config
from services.status_service import emitir_advertencias_falta

def sincronizar_presencas_sheets(reuniao_id):
    import gspread
    import unicodedata
    from pathlib import Path

    def _norm(texto):
        nfkd = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    def _find_field(keys_dict, *keywords):
        for k, v in keys_dict.items():
            for kw in keywords:
                if kw in k:
                    return str(v).strip()
        return ""

    url = get_config("sheets_presenca_url")
    if not url:
        raise ValueError("URL da planilha não configurada. Vá em Configurações → Google Forms.")

    credentials_path = Path(__file__).parent / "credentials.json"
    gc = gspread.service_account(filename=str(credentials_path))
    sh = gc.open_by_url(url)
    ws = sh.sheet1
    records = ws.get_all_records()

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

        matricula = _find_field(keys, "matricula")
        email = _find_field(keys, "email", "mail").lower()
        nome = _find_field(keys, "nome")

        padrinho_id = None

        if matricula and matricula in por_matricula:
            padrinho_id = por_matricula[matricula]
        elif email and email in por_email:
            padrinho_id = por_email[email]
        elif nome and _norm(nome) in por_nome:
            padrinho_id = por_nome[_norm(nome)]

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
    import gspread
    import unicodedata
    from pathlib import Path

    def _norm(texto):
        nfkd = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    def _find_idx(headers_norm, *kws):
        for i, h in enumerate(headers_norm):
            for kw in kws:
                if kw in h:
                    return i
        return None

    url = get_config("sheets_inscricoes_url")
    if not url:
        raise ValueError("URL da planilha de inscrições não configurada. Cole o link em Temas.")

    credentials_path = Path(__file__).parent / "credentials.json"
    gc = gspread.service_account(filename=str(credentials_path))
    sh = gc.open_by_url(url)
    ws = sh.sheet1
    rows = ws.get_all_values()

    if len(rows) < 2:
        return {"atualizados": 0, "nao_reconhecidos": []}

    conn = get_conn()
    padrinhos = conn.execute("SELECT id, nome, matricula FROM padrinhos WHERE ativo=1").fetchall()
    por_nome      = {_norm(p["nome"]): p["id"] for p in padrinhos}
    por_matricula = {str(p["matricula"] or "").strip(): p["id"] for p in padrinhos if p["matricula"]}

    temas_list = conn.execute("SELECT id, titulo FROM temas").fetchall()
    temas_por_titulo = {_norm(t["titulo"]): t["id"] for t in temas_list}

    atualizados = 0
    nao_reconhecidos = []

    header_norm = [_norm(h) for h in rows[0]]

    # Formato Forms response: primeira coluna é timestamp/carimbo
    is_forms = any(kw in header_norm[0] for kw in ("carimbo", "timestamp", "data/hora", "hora"))

    if is_forms:
        idx_nome      = _find_idx(header_norm, "nome")
        idx_matricula = _find_idx(header_norm, "matricula")
        idx_tema      = _find_idx(header_norm, "tema", "apresentar", "inscri", "qual")

        if idx_tema is None:
            conn.close()
            raise ValueError("Coluna de tema não encontrada na planilha de respostas.")

        tema_padrinhos_novos = {}
        for row in rows[1:]:
            if not row or len(row) <= idx_tema:
                continue
            tema_raw = _norm(row[idx_tema].strip())
            tema_id  = temas_por_titulo.get(tema_raw)
            if not tema_id:
                continue

            pid = None
            if idx_matricula is not None and idx_matricula < len(row):
                pid = por_matricula.get(str(row[idx_matricula]).strip())
            if pid is None and idx_nome is not None and idx_nome < len(row):
                pid = por_nome.get(_norm(row[idx_nome].strip()))

            if pid:
                tema_padrinhos_novos.setdefault(tema_id, [])
                if pid not in tema_padrinhos_novos[tema_id]:
                    tema_padrinhos_novos[tema_id].append(pid)
                atualizados += 1
            else:
                nome_str = row[idx_nome].strip() if idx_nome is not None and idx_nome < len(row) else "?"
                if nome_str:
                    nao_reconhecidos.append(nome_str)

        for tema_id, pids in tema_padrinhos_novos.items():
            conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
            for pid in pids:
                conn.execute(
                    "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
                    (tema_id, pid)
                )
    else:
        # Formato tabela: col0 = título do tema, col1+ = nomes/matrículas dos padrinhos
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
            for pid in novos_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
                    (tema_id, pid)
                )

    conn.commit()
    conn.close()
    return {"atualizados": atualizados, "nao_reconhecidos": list(dict.fromkeys(nao_reconhecidos))}


def importar_padrinhos_sheets(url):
    import gspread
    import unicodedata
    from pathlib import Path

    def _norm(texto):
        nfkd = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    def _find_col(keys_norm, *kws):
        for k in keys_norm:
            for kw in kws:
                if kw in k:
                    return k
        return None

    credentials_path = Path(__file__).parent / "credentials.json"
    gc = gspread.service_account(filename=str(credentials_path))
    sh = gc.open_by_url(url)
    ws = sh.sheet1
    records = ws.get_all_records()

    if not records:
        return {"importados": 0, "ignorados": 0, "duplicatas": 0}

    keys_norm = {_norm(k): k for k in records[0].keys()}

    col_nome              = _find_col(keys_norm, "nome")
    col_matricula         = _find_col(keys_norm, "matricula", "matrícula")
    col_email             = _find_col(keys_norm, "email", "e-mail")
    col_telefone          = _find_col(keys_norm, "telefone", "celular", "whatsapp")
    col_turno             = _find_col(keys_norm, "turno")
    col_curso             = _find_col(keys_norm, "curso")
    col_instituicao       = _find_col(keys_norm, "institui", "universidade", "faculdade")
    col_cidade            = _find_col(keys_norm, "cidade", "grande bh", "bh")
    col_bolsista          = _find_col(keys_norm, "bolsista", "prouni", "pro-uni")
    col_trabalha          = _find_col(keys_norm, "trabalha", "trabalho", "emprego")
    col_idade             = _find_col(keys_norm, "idade")
    col_periodo           = _find_col(keys_norm, "periodo", "período", "semestre cursando")
    col_passou_algoritmos = _find_col(keys_norm, "algoritmo", "aeds", "introducao", "introdução", "intro a alg")

    def _get(rec, col):
        return str(rec.get(keys_norm.get(col, ""), "") or "").strip() if col else ""

    conn = get_conn()
    existing = {str(p["matricula"]).strip(): True
                for p in conn.execute("SELECT matricula FROM padrinhos").fetchall()
                if p["matricula"]}

    importados = ignorados = duplicatas = 0

    for rec in records:
        curso = _norm(_get(rec, col_curso))
        inst  = _norm(_get(rec, col_instituicao))

        if "engenharia de software" not in curso or "puc" not in inst:
            ignorados += 1
            continue

        matricula = _get(rec, col_matricula)
        if matricula and matricula in existing:
            duplicatas += 1
            continue

        nome     = _get(rec, col_nome)
        email    = _get(rec, col_email)
        telefone = _get(rec, col_telefone)
        turno    = _get(rec, col_turno)
        idade_s  = _get(rec, col_idade)
        idade    = int(idade_s) if idade_s.isdigit() else None

        cidade_raw = _norm(_get(rec, col_cidade))
        cidade_bh  = 1 if ("sim" in cidade_raw or "grande bh" in cidade_raw or "bh" in cidade_raw) else 0

        bolsista_raw = _norm(_get(rec, col_bolsista))
        bolsista     = 1 if "sim" in bolsista_raw else 0

        trabalha_raw = _norm(_get(rec, col_trabalha))
        trabalha     = 1 if "sim" in trabalha_raw else 0

        periodo = _get(rec, col_periodo) or None

        passou_raw       = _norm(_get(rec, col_passou_algoritmos))
        passou_algoritmos = 1 if "sim" in passou_raw else (0 if passou_raw else None)

        if not nome:
            ignorados += 1
            continue

        conn.execute("""
            INSERT INTO padrinhos (nome, matricula, email, telefone, turno, idade, cidade_bh, bolsista, trabalha, periodo, passou_algoritmos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, matricula or None, email or None, telefone or None,
              turno or None, idade, cidade_bh, bolsista, trabalha, periodo, passou_algoritmos))

        if matricula:
            existing[matricula] = True
        importados += 1

    conn.commit()
    conn.close()
    return {"importados": importados, "ignorados": ignorados, "duplicatas": duplicatas}


def importar_calouros_sheets(url):
    import gspread
    import unicodedata
    from pathlib import Path

    def _norm(texto):
        nfkd = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    def _find_col(keys_norm, *kws):
        for k in keys_norm:
            for kw in kws:
                if kw in k:
                    return k
        return None

    credentials_path = Path(__file__).parent / "credentials.json"
    gc = gspread.service_account(filename=str(credentials_path))
    sh = gc.open_by_url(url)
    ws = sh.sheet1
    records = ws.get_all_records()

    if not records:
        return {"importados": 0, "ignorados": 0, "duplicatas": 0}

    keys_norm = {_norm(k): k for k in records[0].keys()}

    col_nome            = _find_col(keys_norm, "nome")
    col_telefone        = _find_col(keys_norm, "telefone", "celular", "whatsapp")
    col_turno           = _find_col(keys_norm, "turno")
    col_curso           = _find_col(keys_norm, "curso")
    col_instituicao     = _find_col(keys_norm, "institui", "universidade", "faculdade")
    col_cidade          = _find_col(keys_norm, "cidade", "grande bh", "bh")
    col_bolsista        = _find_col(keys_norm, "bolsista", "prouni", "pro-uni")
    col_trabalha        = _find_col(keys_norm, "trabalha", "trabalho", "emprego")
    col_idade           = _find_col(keys_norm, "idade")
    col_primeiro_periodo = _find_col(keys_norm, "primeiro periodo", "1o periodo", "1º periodo", "primeiro per")

    def _get(rec, col):
        return str(rec.get(keys_norm.get(col, ""), "") or "").strip() if col else ""

    conn = get_conn()
    existing_nomes = {_norm(c["nome"]): True
                      for c in conn.execute("SELECT nome FROM calouros").fetchall()}

    importados = ignorados = duplicatas = 0

    for rec in records:
        curso = _norm(_get(rec, col_curso))
        inst  = _norm(_get(rec, col_instituicao))

        if "engenharia de software" not in curso or "puc" not in inst:
            ignorados += 1
            continue

        nome = _get(rec, col_nome)
        if not nome:
            ignorados += 1
            continue

        if _norm(nome) in existing_nomes:
            duplicatas += 1
            continue

        telefone  = _get(rec, col_telefone)
        turno     = _get(rec, col_turno)
        idade_s   = _get(rec, col_idade)
        idade     = int(idade_s) if idade_s.isdigit() else None

        cidade_raw = _norm(_get(rec, col_cidade))
        cidade_bh  = 1 if ("sim" in cidade_raw or "grande bh" in cidade_raw or "bh" in cidade_raw) else 0

        bolsista_raw = _norm(_get(rec, col_bolsista))
        bolsista     = 1 if "sim" in bolsista_raw else 0

        trabalha_raw = _norm(_get(rec, col_trabalha))
        trabalha     = 1 if "sim" in trabalha_raw else 0

        primeiro_raw     = _norm(_get(rec, col_primeiro_periodo))
        primeiro_periodo = 1 if "sim" in primeiro_raw else (0 if primeiro_raw else None)

        conn.execute("""
            INSERT INTO calouros (nome, telefone, turno, idade, cidade_bh, bolsista, trabalha, primeiro_periodo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, telefone or None, turno or None, idade, cidade_bh, bolsista, trabalha, primeiro_periodo))

        existing_nomes[_norm(nome)] = True
        importados += 1

    conn.commit()
    conn.close()
    return {"importados": importados, "ignorados": ignorados, "duplicatas": duplicatas}


def importar_presencas_csv(caminho_csv, reuniao_id):
    import csv

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

    todos_padrinhos = conn.execute(
        "SELECT id, matricula FROM padrinhos WHERE ativo=1"
    ).fetchall()
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
            (reuniao_id, p["id"])
        ).fetchone()
        if not registro:
            conn.execute("""
                INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
                VALUES (?, ?, 0, 0)
            """, (reuniao_id, p["id"]))

    conn.commit()
    emitir_advertencias_falta(reuniao_id)
    conn.close()

    return {
        "processados": processados,
        "nao_encontrados": nao_encontrados,
    }
