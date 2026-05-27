import json
import os
from database import get_conn
from datetime import date, datetime

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_semestre.json")

_CONFIG_DEFAULTS = {
    "semestre": "2026/1",
    "professor_coordenador": "Prof. Laerte Xavier",
    "programa": "Mentoria Acadêmica — Engenharia de Software",
    "instituicao": "PUC Minas",
    "total_reunioes": 3,
    "data_inicio": "2026-03-01",
    "data_fim": "2026-07-15",
    "coordenadora_geral": "",
    "coordenadores": [],
}

def get_config_semestre():
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            loaded = json.load(f)
        return {**_CONFIG_DEFAULTS, **loaded}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_CONFIG_DEFAULTS)

def salvar_config_semestre(dados):
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

_PREPS = {"de", "da", "do", "dos", "das", "e", "di", "von", "van", "el"}

def abreviar_nome(nome):
    if not nome:
        return nome
    partes = nome.split()
    if len(partes) <= 2:
        return nome
    primeiro = partes[0]
    ultimo_idx = len(partes) - 1
    while ultimo_idx > 0 and partes[ultimo_idx].lower() in _PREPS:
        ultimo_idx -= 1
    ultimo = partes[ultimo_idx]
    meios = [p[0].upper() + '.' for p in partes[1:ultimo_idx] if p.lower() not in _PREPS]
    if meios:
        return primeiro + ' ' + ' '.join(meios) + ' ' + ultimo
    return primeiro + ' ' + ultimo

def registrar_log(acao, descricao):
    from flask import request as _req
    conn = get_conn()
    try:
        ip = _req.remote_addr
    except RuntimeError:
        ip = None
    conn.execute(
        "INSERT INTO logs (acao, descricao, data, ip) VALUES (?, ?, ?, ?)",
        (acao, descricao, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip)
    )
    conn.commit()
    conn.close()

def get_todos_padrinhos():
    conn = get_conn()
    padrinhos = conn.execute(
        "SELECT * FROM padrinhos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    conn.close()
    return padrinhos

def get_padrinho(padrinho_id):
    conn = get_conn()
    padrinho = conn.execute(
        "SELECT * FROM padrinhos WHERE id = ?", (padrinho_id,)
    ).fetchone()
    conn.close()
    return padrinho

def cadastrar_padrinho(nome, matricula, email, telefone, turno):
    conn = get_conn()
    conn.execute(
        "INSERT INTO padrinhos (nome, matricula, email, telefone, turno) VALUES (?, ?, ?, ?, ?)",
        (nome, matricula, email, telefone, turno)
    )
    conn.commit()
    conn.close()

def get_todas_reunioes():
    conn = get_conn()
    reunioes = conn.execute(
        "SELECT * FROM reunioes ORDER BY data DESC"
    ).fetchall()
    conn.close()
    return reunioes

def contar_reunioes():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM reunioes").fetchone()[0]
    conn.close()
    return count

def criar_reuniao(data, tema, descricao):
    conn = get_conn()
    conn.execute(
        "INSERT INTO reunioes (data, tema, descricao) VALUES (?, ?, ?)",
        (data, tema, descricao)
    )
    conn.commit()
    conn.close()

def lancar_presenca(reuniao_id, padrinho_id, presente, justificada):
    conn = get_conn()
    conn.execute("""
        INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(reuniao_id, padrinho_id)
        DO UPDATE SET presente = excluded.presente, justificada = excluded.justificada
    """, (reuniao_id, padrinho_id, presente, justificada))
    conn.commit()
    conn.close()

def get_presencas_reuniao(reuniao_id):
    conn = get_conn()
    presencas = conn.execute("""
        SELECT p.id, p.nome, p.matricula,
               COALESCE(pr.presente, 0)    AS presente,
               COALESCE(pr.justificada, 0) AS justificada
        FROM padrinhos p
        LEFT JOIN presencas pr
               ON pr.padrinho_id = p.id AND pr.reuniao_id = ?
        WHERE p.ativo = 1
        ORDER BY p.nome
    """, (reuniao_id,)).fetchall()
    conn.close()
    return presencas

def get_todos_temas():
    from collections import defaultdict
    conn = get_conn()
    temas = conn.execute(
        "SELECT * FROM temas ORDER BY data_limite ASC"
    ).fetchall()
    rows = conn.execute("""
        SELECT tp.tema_id, p.id, p.nome
        FROM tema_padrinhos tp
        JOIN padrinhos p ON p.id = tp.padrinho_id
        ORDER BY p.nome
    """).fetchall()
    conn.close()
    padrinhos_por_tema = defaultdict(list)
    for row in rows:
        padrinhos_por_tema[row["tema_id"]].append({"id": row["id"], "nome": row["nome"]})
    return [{"tema": t, "padrinhos": padrinhos_por_tema[t["id"]]} for t in temas]

def registrar_tema(titulo, data_aviso, data_limite, padrinho_ids):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO temas (titulo, data_aviso, data_limite) VALUES (?, ?, ?)",
        (titulo, data_aviso, data_limite)
    )
    tema_id = cur.lastrowid
    for pid in padrinho_ids:
        conn.execute(
            "INSERT INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
            (tema_id, pid)
        )
    conn.commit()
    conn.close()

def _emitir_advertencias_tema(conn, tema_id, tipo, origem, motivo):
    padrinhos = conn.execute(
        "SELECT padrinho_id FROM tema_padrinhos WHERE tema_id = ?", (tema_id,)
    ).fetchall()
    for p in padrinhos:
        conn.execute("""
            INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
            VALUES (?, ?, ?, ?, ?)
        """, (p["padrinho_id"], tipo, origem, motivo, date.today().isoformat()))


def registrar_entrega_tema(tema_id, data_entrega_str):
    conn = get_conn()
    tema = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()

    if tema["situacao"] not in (None, "pendente"):
        conn.close()
        return tema["situacao"]

    data_limite  = datetime.strptime(tema["data_limite"], "%Y-%m-%d").date()
    data_entrega = datetime.strptime(data_entrega_str, "%Y-%m-%d").date()
    diff = (data_entrega - data_limite).days

    if diff <= 0:
        situacao = "entregue"
    elif diff == 1:
        situacao = "atraso"
    else:
        situacao = "nao_entregue"

    conn.execute(
        "UPDATE temas SET data_entrega = ?, situacao = ? WHERE id = ?",
        (data_entrega_str, situacao, tema_id)
    )

    if situacao == "atraso":
        _emitir_advertencias_tema(conn, tema_id, "amarelo", "atraso_tema",
                                  f"Entrega com atraso: {tema['titulo']}")
    elif situacao == "nao_entregue":
        _emitir_advertencias_tema(conn, tema_id, "vermelho", "nao_entrega",
                                  f"Não entregou: {tema['titulo']}")

    conn.commit()
    conn.close()
    return situacao

def marcar_tema_nao_entregue(tema_id):
    conn = get_conn()
    tema = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()

    if tema["situacao"] not in (None, "pendente"):
        conn.close()
        return

    conn.execute(
        "UPDATE temas SET situacao = 'nao_entregue' WHERE id = ?", (tema_id,)
    )
    _emitir_advertencias_tema(conn, tema_id, "vermelho", "nao_entrega",
                              f"Não entregou: {tema['titulo']}")
    conn.commit()
    conn.close()

def emitir_advertencias_falta(reuniao_id):
    conn = get_conn()
    ausentes = conn.execute("""
        SELECT padrinho_id FROM presencas
        WHERE reuniao_id = ? AND presente = 0 AND justificada = 0
    """, (reuniao_id,)).fetchall()
    motivo = f"Falta sem justificativa — reunião {reuniao_id}"
    for row in ausentes:
        existente = conn.execute(
            "SELECT id FROM advertencias WHERE padrinho_id=? AND motivo=?",
            (row["padrinho_id"], motivo)
        ).fetchone()
        if not existente:
            conn.execute("""
                INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
                VALUES (?, 'amarelo', 'falta', ?, ?)
            """, (row["padrinho_id"], motivo, date.today().isoformat()))
    conn.commit()
    conn.close()

def emitir_advertencia_manual(padrinho_id, motivo, tipo='vermelho'):
    conn = get_conn()
    conn.execute("""
        INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
        VALUES (?, ?, 'manual', ?, ?)
    """, (padrinho_id, tipo, motivo, date.today().isoformat()))
    conn.commit()
    conn.close()

def get_advertencias_padrinho(padrinho_id):
    conn = get_conn()
    advertencias = conn.execute(
        "SELECT * FROM advertencias WHERE padrinho_id = ? ORDER BY data DESC",
        (padrinho_id,)
    ).fetchall()
    conn.close()
    return advertencias

def get_config(chave, padrao=None):
    conn = get_conn()
    row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return row["valor"] if row else padrao

def set_config(chave, valor):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()

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

def calcular_status(padrinho_id, limite=None):
    conn = get_conn()
    rows = conn.execute(
        "SELECT tipo, COUNT(*) AS cnt FROM advertencias WHERE padrinho_id = ? GROUP BY tipo",
        (padrinho_id,)
    ).fetchall()
    conn.close()
    counts = {r["tipo"]: r["cnt"] for r in rows}
    amarelos = counts.get("amarelo", 0)
    vermelhos = counts.get("vermelho", 0)

    if limite is None:
        limite = contar_reunioes()

    if vermelhos >= 1:
        return {"status": "inapto_vermelho", "amarelos": amarelos, "vermelhos": vermelhos}
    if limite > 0 and amarelos >= limite:
        return {"status": "inapto_amarelo", "amarelos": amarelos, "vermelhos": vermelhos}
    if limite > 0 and amarelos == limite - 1:
        return {"status": "alerta", "amarelos": amarelos, "vermelhos": vermelhos}
    return {"status": "apto", "amarelos": amarelos, "vermelhos": vermelhos}

def get_historico_padrinho(padrinho_id):
    conn = get_conn()
    presencas = conn.execute("""
        SELECT r.data, r.tema, pr.presente, pr.justificada
        FROM presencas pr
        JOIN reunioes r ON r.id = pr.reuniao_id
        WHERE pr.padrinho_id = ?
        ORDER BY r.data DESC
    """, (padrinho_id,)).fetchall()
    temas = conn.execute("""
        SELECT t.titulo, t.data_limite, t.data_entrega, t.situacao
        FROM temas t
        JOIN tema_padrinhos tp ON tp.tema_id = t.id
        WHERE tp.padrinho_id = ?
        ORDER BY t.data_limite DESC
    """, (padrinho_id,)).fetchall()
    conn.close()
    return {"presencas": presencas, "temas": temas}

def calcular_todos_status(padrinho_ids, limite=None):
    """Bulk calcular_status — 2 queries instead of 2N."""
    if not padrinho_ids:
        return {}
    if limite is None:
        limite = contar_reunioes()
    conn = get_conn()
    ph = ",".join("?" * len(padrinho_ids))
    rows = conn.execute(
        f"SELECT padrinho_id, tipo, COUNT(*) AS cnt FROM advertencias "
        f"WHERE padrinho_id IN ({ph}) GROUP BY padrinho_id, tipo",
        list(padrinho_ids)
    ).fetchall()
    conn.close()
    counts = {}
    for r in rows:
        pid = r["padrinho_id"]
        if pid not in counts:
            counts[pid] = {}
        counts[pid][r["tipo"]] = r["cnt"]
    result = {}
    for pid in padrinho_ids:
        c = counts.get(pid, {})
        amarelos  = c.get("amarelo", 0)
        vermelhos = c.get("vermelho", 0)
        if vermelhos >= 1:
            status = "inapto_vermelho"
        elif limite > 0 and amarelos >= limite:
            status = "inapto_amarelo"
        elif limite > 0 and amarelos == limite - 1:
            status = "alerta"
        else:
            status = "apto"
        result[pid] = {"status": status, "amarelos": amarelos, "vermelhos": vermelhos}
    return result


def get_relatorio_geral():
    padrinhos = get_todos_padrinhos()
    if not padrinhos:
        return []
    padrinho_ids = [p["id"] for p in padrinhos]
    limite = contar_reunioes()
    todos_status = calcular_todos_status(padrinho_ids, limite)
    conn = get_conn()
    ph = ",".join("?" * len(padrinho_ids))
    pres_rows = conn.execute(
        f"SELECT padrinho_id, COUNT(*) AS total, SUM(presente) AS presentes "
        f"FROM presencas WHERE padrinho_id IN ({ph}) GROUP BY padrinho_id",
        padrinho_ids
    ).fetchall()
    conn.close()
    pres_map = {r["padrinho_id"]: (r["total"], r["presentes"] or 0) for r in pres_rows}
    relatorio = []
    for p in padrinhos:
        st = todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})
        total_r, presentes = pres_map.get(p["id"], (0, 0))
        relatorio.append({
            "padrinho":        p,
            "status":          st["status"],
            "amarelos":        st["amarelos"],
            "vermelhos":       st["vermelhos"],
            "total_reunioes":  total_r,
            "total_presentes": presentes,
        })
    return relatorio

def exportar_relatorio_csv(caminho="relatorio_acg.csv"):
    import csv
    dados = get_relatorio_geral()
    headers = ["Nome", "Matricula", "Email", "Telefone", "Turno",
               "Reunioes", "Presencas", "Amarelos", "Vermelhos", "Status"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for d in dados:
            w.writerow([
                d["padrinho"]["nome"],
                d["padrinho"]["matricula"],
                d["padrinho"]["email"] or "",
                d["padrinho"]["telefone"] or "",
                d["padrinho"]["turno"] or "",
                d["total_reunioes"],
                d["total_presentes"],
                d["amarelos"],
                d["vermelhos"],
                d["status"],
            ])
    return caminho


def get_calouros_match_completo():
    from collections import defaultdict
    conn = get_conn()
    padrinhos = conn.execute(
        "SELECT * FROM padrinhos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    rows = conn.execute("""
        SELECT m.padrinho_id, c.id, c.nome, c.telefone
        FROM matches m
        JOIN calouros c ON c.id = m.calouro_id
        ORDER BY c.nome
    """).fetchall()
    conn.close()
    calouros_por_padrinho = defaultdict(list)
    for row in rows:
        calouros_por_padrinho[row["padrinho_id"]].append(
            {"id": row["id"], "nome": row["nome"], "telefone": row["telefone"]}
        )
    return [{"padrinho": p, "calouros": calouros_por_padrinho[p["id"]]} for p in padrinhos]

def editar_padrinho(padrinho_id, nome, matricula, email, telefone, turno,
                    genero=None, idade=None, cidade_bh=None, bolsista=None,
                    trabalha=None, periodo=None, passou_algoritmos=None):
    conn = get_conn()
    conn.execute("""
        UPDATE padrinhos
        SET nome=?, matricula=?, email=?, telefone=?, turno=?,
            genero=?, idade=?, cidade_bh=?, bolsista=?, trabalha=?,
            periodo=?, passou_algoritmos=?
        WHERE id=?
    """, (nome, matricula, email, telefone, turno,
          genero, idade, cidade_bh, bolsista, trabalha,
          periodo, passou_algoritmos, padrinho_id))
    conn.commit()
    conn.close()

def excluir_padrinho(padrinho_id):
    conn = get_conn()
    conn.execute("UPDATE padrinhos SET ativo=0 WHERE id=?", (padrinho_id,))
    conn.commit()
    conn.close()

def redistribuir_calouros(padrinho_id, redistribuicao):
    """Reassigns calouros and marks padrinho inactive. redistribuicao: {calouro_id: novo_padrinho_id}"""
    conn = get_conn()
    for calouro_id, novo_padrinho_id in redistribuicao.items():
        if novo_padrinho_id:
            conn.execute(
                "UPDATE matches SET padrinho_id=? WHERE calouro_id=? AND padrinho_id=?",
                (int(novo_padrinho_id), int(calouro_id), padrinho_id)
            )
        else:
            conn.execute(
                "DELETE FROM matches WHERE calouro_id=? AND padrinho_id=?",
                (int(calouro_id), padrinho_id)
            )
    conn.execute("UPDATE padrinhos SET ativo=0 WHERE id=?", (padrinho_id,))
    conn.commit()
    conn.close()

def excluir_advertencia(advertencia_id):
    conn = get_conn()
    conn.execute("DELETE FROM advertencias WHERE id=?", (advertencia_id,))
    conn.commit()
    conn.close()


def excluir_reuniao(reuniao_id):
    conn = get_conn()
    conn.execute("DELETE FROM presencas WHERE reuniao_id=?", (reuniao_id,))
    conn.execute("DELETE FROM reunioes WHERE id=?", (reuniao_id,))
    conn.commit()
    conn.close()

def excluir_tema(tema_id):
    conn = get_conn()
    conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
    conn.execute("DELETE FROM temas WHERE id=?", (tema_id,))
    conn.commit()
    conn.close()

def editar_reuniao(reuniao_id, data, tema, descricao):
    conn = get_conn()
    conn.execute(
        "UPDATE reunioes SET data=?, tema=?, descricao=? WHERE id=?",
        (data, tema, descricao, reuniao_id)
    )
    conn.commit()
    conn.close()

def editar_tema(tema_id, titulo, data_aviso, data_limite, padrinho_ids):
    conn = get_conn()
    conn.execute(
        "UPDATE temas SET titulo=?, data_aviso=?, data_limite=? WHERE id=?",
        (titulo, data_aviso, data_limite, tema_id)
    )
    conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
    for pid in padrinho_ids:
        conn.execute(
            "INSERT INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
            (tema_id, pid)
        )
    conn.commit()
    conn.close()

def rodar_match(max_calouros=3, score_minimo=0):
    conn = get_conn()
    padrinhos = [dict(p) for p in conn.execute(
        "SELECT * FROM padrinhos WHERE ativo=1 ORDER BY nome"
    ).fetchall()]
    calouros = [dict(c) for c in conn.execute(
        "SELECT * FROM calouros ORDER BY nome"
    ).fetchall()]
    conn.close()

    def _score(p, c):
        s = 0
        if p.get("turno") and c.get("turno") and p["turno"] == c["turno"]:
            s += 200
        if p.get("genero") and c.get("genero") and p["genero"] == c["genero"]:
            s += 80
        if p.get("cidade_bh") and c.get("cidade_bh"):
            s += 4
        if p.get("bolsista") and c.get("bolsista"):
            s += 2
        if p.get("trabalha") and c.get("trabalha"):
            s += 1
        pi, ci = p.get("idade"), c.get("idade")
        if pi and ci:
            diff = abs(int(pi) - int(ci))
            if diff <= 2:
                s += 8
            elif diff <= 5:
                s += 4
        return s

    atribuicoes = {p["id"]: [] for p in padrinhos}
    sem_match = []

    for c in calouros:
        candidatos = []
        for p in padrinhos:
            n = len(atribuicoes[p["id"]])
            if n >= max_calouros:
                continue
            s = _score(p, c) - n * 10  # penalidade progressiva
            candidatos.append((s, p))

        if not candidatos:
            sem_match.append({"calouro": c, "motivo": "Sem vagas disponíveis"})
            continue

        candidatos.sort(key=lambda x: -x[0])
        melhor_score, melhor_p = candidatos[0]

        if melhor_score < score_minimo:
            sem_match.append({"calouro": c, "motivo": f"Score {melhor_score} abaixo do mínimo configurado"})
            continue

        atribuicoes[melhor_p["id"]].append({"calouro": c, "score": melhor_score})

    resultado = [
        {
            "padrinho": p,
            "calouros": atribuicoes[p["id"]],
            "total": len(atribuicoes[p["id"]]),
            "score_medio": round(
                sum(x["score"] for x in atribuicoes[p["id"]]) / len(atribuicoes[p["id"]])
            ) if atribuicoes[p["id"]] else 0,
        }
        for p in padrinhos
    ]
    return {"resultado": resultado, "sem_match": sem_match}


def _pdf_helpers(W):
    """Retorna funções auxiliares compartilhadas pelos PDFs."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import Paragraph, Table, TableStyle

    SLATE_BG  = HexColor('#f8fafc')
    STRIPE    = HexColor('#f1f5f9')
    BORDER    = HexColor('#e2e8f0')
    SLATE_TXT = HexColor('#64748b')
    BODY_TXT  = HexColor('#1e293b')

    def _p(text, font="Helvetica", size=9, color=BODY_TXT, align=TA_CENTER):
        return Paragraph(
            f'<font name="{font}" size="{size}">{text}</font>',
            ParagraphStyle("_", fontName=font, fontSize=size, textColor=color, alignment=align))

    def _data_table(headers, rows, col_widths, stripe=STRIPE, border=BORDER):
        cell_style = ParagraphStyle("_cell", fontName="Helvetica", fontSize=9,
                                    textColor=BODY_TXT, alignment=TA_LEFT)
        def _cell(val): return Paragraph(str(val) if val else "-", cell_style)
        header_cells = [_p(h, "Helvetica-Bold", 7, SLATE_TXT) for h in headers]
        raw_body = rows if rows else [["Nenhum registro."] + [""] * (len(headers) - 1)]
        body = [[_cell(v) for v in row] for row in raw_body]
        data = [header_cells] + body
        style = [
            ("BACKGROUND",    (0, 0), (-1, 0),  SLATE_BG),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.5, border),
            ("GRID",          (0, 0), (-1, -1), 0.4, border),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i in range(2, len(data), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), stripe))
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle(style))
        return t

    def _section_header(label, bg, text_color):
        t = Table([[_p(label, "Helvetica-Bold", 10, text_color)]], colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BORDER),
        ]))
        return t

    def _page_header(title_left, subtitle_right, bg_color):
        from reportlab.lib.colors import white
        from reportlab.lib.enums import TA_RIGHT, TA_LEFT
        t = Table([[
            _p(title_left, "Helvetica-Bold", 16, white, TA_LEFT),
            _p(subtitle_right, "Helvetica", 10, white, TA_RIGHT),
        ]], colWidths=[W * 0.5, W * 0.5])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING",   (0, 0), (0, -1),  16),
            ("RIGHTPADDING",  (-1, 0), (-1, -1), 16),
        ]))
        return t

    def _sig_block(left_label, right_label):
        from reportlab.lib.enums import TA_CENTER
        sig = Table([[
            _p("_" * 38, "Helvetica", 10, SLATE_TXT, TA_CENTER),
            _p("", "Helvetica", 10, SLATE_TXT),
            _p("_" * 38, "Helvetica", 10, SLATE_TXT, TA_CENTER),
        ]], colWidths=[W * 0.44, W * 0.12, W * 0.44])
        sig_labels = Table([[
            _p(left_label, "Helvetica", 8, SLATE_TXT, TA_CENTER),
            _p("", "Helvetica", 8, SLATE_TXT),
            _p(right_label, "Helvetica", 8, SLATE_TXT, TA_CENTER),
        ]], colWidths=[W * 0.44, W * 0.12, W * 0.44])
        return sig, sig_labels

    def _footer(text):
        t = Table([[_p(text, "Helvetica", 7, HexColor('#94a3b8'))]], colWidths=[W])
        t.setStyle(TableStyle([
            ("LINEABOVE",     (0, 0), (-1, 0),  0.5, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    return _p, _data_table, _section_header, _page_header, _sig_block, _footer


def gerar_pdf_acg():
    """Relatório 1: Aptidão ACG — lista completa para emissão de ACG."""
    cfg = get_config_semestre()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Spacer
    import io
    from datetime import date as _date

    hoje = _date.today().strftime("%d/%m/%Y")
    dados = get_relatorio_geral()

    aptos            = [d for d in dados if d["status"] == "apto"]
    inaptos_amarelo  = [d for d in dados if d["status"] == "inapto_amarelo"]
    inaptos_vermelho = [d for d in dados if d["status"] == "inapto_vermelho"]

    VIOLET     = HexColor('#5b3df5')
    VERDE_BG   = HexColor('#dcfce7')
    LARANJA_BG = HexColor('#ffedd5')
    VERM_BG    = HexColor('#fee2e2')
    BORDER     = HexColor('#e2e8f0')

    W = A4[0] - 4 * cm
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title="Relatório de Aptidão ACG — Padrinho Track")

    _p, _dt, _sh, _ph, _sig, _ft = _pdf_helpers(W)

    story = []

    story.append(_ph(
        "<b>PADRINHO</b> <font color='#a78bfa'>TRACK</font>",
        f"Aptidão ACG — {cfg['semestre']}<br/>"
        f"<font size='8'>{cfg['instituicao']}   |   Gerado em {hoje}</font>",
        VIOLET
    ))
    story.append(Spacer(1, 0.5 * cm))

    from reportlab.platypus import Table, TableStyle
    summary = Table([[
        _p(f"<b>{len(dados)}</b><br/>Inscritos", "Helvetica-Bold", 11, HexColor('#1e3a5f')),
        _p(f"<b>{len(aptos)}</b><br/>Aptos", "Helvetica-Bold", 11, HexColor('#166534')),
        _p(f"<b>{len(inaptos_amarelo)}</b><br/>Inaptos", "Helvetica-Bold", 11, HexColor('#c2410c')),
        _p(f"<b>{len(inaptos_vermelho)}</b><br/>Inaptos Graves", "Helvetica-Bold", 11, HexColor('#991b1b')),
    ]], colWidths=[W / 4] * 4)
    summary.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  HexColor('#eff6ff')),
        ("BACKGROUND",    (1, 0), (1, -1),  HexColor('#f0fdf4')),
        ("BACKGROUND",    (2, 0), (2, -1),  HexColor('#fff7ed')),
        ("BACKGROUND",    (3, 0), (3, -1),  HexColor('#fff1f2')),
        ("BOX",           (0, 0), (0, -1),  0.8, HexColor('#bfdbfe')),
        ("BOX",           (1, 0), (1, -1),  0.8, HexColor('#bbf7d0')),
        ("BOX",           (2, 0), (2, -1),  0.8, HexColor('#fed7aa')),
        ("BOX",           (3, 0), (3, -1),  0.8, HexColor('#fecdd3')),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary)
    story.append(Spacer(1, 0.6 * cm))

    story.append(_sh(f"APTOS PARA EMISSÃO DE ACG  ({len(aptos)})", VERDE_BG, HexColor('#166534')))
    story.append(Spacer(1, 0.15 * cm))
    rows_a = [[d["padrinho"]["nome"], d["padrinho"]["matricula"],
               d["padrinho"]["turno"] or "-",
               f"{d['total_presentes']}/{d['total_reunioes']}"]
              for d in aptos]
    story.append(_dt(["Nome Completo", "Matrícula", "Turno", "Presenças"], rows_a,
                     [W * 0.44, W * 0.20, W * 0.16, W * 0.20]))
    story.append(Spacer(1, 0.5 * cm))

    if inaptos_amarelo:
        story.append(_sh(f"INAPTOS  ({len(inaptos_amarelo)})", LARANJA_BG, HexColor('#c2410c')))
        story.append(Spacer(1, 0.15 * cm))
        rows_am = [[d["padrinho"]["nome"], d["padrinho"]["matricula"],
                    f"{d['amarelos']} amarelo{'s' if d['amarelos'] != 1 else ''}"]
                   for d in inaptos_amarelo]
        story.append(_dt(["Nome", "Matrícula", "Amarelos"], rows_am,
                         [W * 0.55, W * 0.25, W * 0.20]))
        story.append(Spacer(1, 0.5 * cm))

    if inaptos_vermelho:
        conn = get_conn()
        rows_v = []
        for d in inaptos_vermelho:
            adv = conn.execute(
                "SELECT motivo FROM advertencias WHERE padrinho_id=? AND tipo='vermelho' ORDER BY data DESC LIMIT 1",
                (d["padrinho"]["id"],)).fetchone()
            rows_v.append([d["padrinho"]["nome"], d["padrinho"]["matricula"], adv["motivo"] if adv else "-"])
        conn.close()
        story.append(_sh(f"INAPTOS GRAVES  ({len(inaptos_vermelho)})", VERM_BG, HexColor('#991b1b')))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_dt(["Nome", "Matrícula", "Motivo"], rows_v, [W * 0.35, W * 0.20, W * 0.45]))
        story.append(Spacer(1, 0.6 * cm))

    story.append(Spacer(1, 0.6 * cm))
    sig, sig_labels = _sig(
        f"Professor Coordenador\n{cfg['professor_coordenador']}",
        "Responsável pelo Programa\n "
    )
    story.append(sig)
    story.append(sig_labels)
    story.append(Spacer(1, 0.4 * cm))
    story.append(_ft(f"Gerado pelo Padrinho Track  |  {cfg['instituicao']}  |  {cfg['programa']}  |  {hoje}"))

    doc.build(story)
    return buf.getvalue()


def gerar_pdf_resumo_semestre():
    """Relatório 2: Resumo do semestre — cronograma, totais e resultado."""
    cfg = get_config_semestre()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle
    import io
    from datetime import date as _date

    hoje = _date.today().strftime("%d/%m/%Y")
    dados      = get_relatorio_geral()
    temas_lista = get_todos_temas()
    padrinhos  = get_todos_padrinhos()
    reunioes   = get_todas_reunioes()

    conn = get_conn()
    total_calouros = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    conn.close()

    aptos            = [d for d in dados if d["status"] == "apto"]
    alertas          = [d for d in dados if d["status"] == "alerta"]
    inaptos_amarelo  = [d for d in dados if d["status"] == "inapto_amarelo"]
    inaptos_vermelho = [d for d in dados if d["status"] == "inapto_vermelho"]

    VIOLET    = HexColor('#5b3df5')
    INDIGO_BG = HexColor('#eef2ff')
    BORDER    = HexColor('#e2e8f0')
    SLATE_TXT = HexColor('#64748b')

    W = A4[0] - 4 * cm
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title="Resumo do Semestre — Padrinho Track")

    _p, _dt, _sh, _ph, _sig, _ft = _pdf_helpers(W)

    story = []

    story.append(_ph(
        "<b>PADRINHO</b> <font color='#a78bfa'>TRACK</font>",
        f"Resumo do Semestre — {cfg['semestre']}<br/>"
        f"<font size='8'>{cfg['instituicao']}   |   {hoje}</font>",
        VIOLET
    ))
    story.append(Spacer(1, 0.4 * cm))

    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    info_style = ParagraphStyle("_info", fontName="Helvetica", fontSize=9,
                                textColor=HexColor('#1e293b'), alignment=TA_LEFT)

    def _info_row(label, value):
        from reportlab.platypus import Paragraph as P
        return [P(f'<font name="Helvetica-Bold" color="#64748b">{label}</font>', info_style),
                P(str(value), info_style)]

    info_data = [
        _info_row("Semestre", cfg["semestre"]),
        _info_row("Professor coordenador", cfg["professor_coordenador"]),
        _info_row("Programa", cfg["programa"]),
        _info_row("Período", f"{cfg.get('data_inicio','—')}  →  {cfg.get('data_fim','—')}"),
    ]
    info_table = Table(info_data, colWidths=[W * 0.22, W * 0.78])
    info_table.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.5, BORDER),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    summary = Table([[
        _p(f"<b>{len(padrinhos)}</b><br/>Padrinhos", "Helvetica-Bold", 11, HexColor('#1e3a5f')),
        _p(f"<b>{total_calouros}</b><br/>Calouros", "Helvetica-Bold", 11, HexColor('#1e3a5f')),
        _p(f"<b>{len(reunioes)}</b><br/>Reuniões", "Helvetica-Bold", 11, SLATE_TXT),
        _p(f"<b>{len(temas_lista)}</b><br/>Temas", "Helvetica-Bold", 11, SLATE_TXT),
    ]], colWidths=[W / 4] * 4)
    summary.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (1, -1),  HexColor('#eff6ff')),
        ("BACKGROUND",    (2, 0), (3, -1),  HexColor('#f8fafc')),
        ("BOX",           (0, 0), (1, -1),  0.8, HexColor('#bfdbfe')),
        ("BOX",           (2, 0), (3, -1),  0.8, BORDER),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary)
    story.append(Spacer(1, 0.5 * cm))

    story.append(_sh("CRONOGRAMA DE TEMAS", INDIGO_BG, HexColor('#312e81')))
    story.append(Spacer(1, 0.15 * cm))
    _sit = {"pendente": "Pendente", "entregue": "Entregue",
            "atraso": "Atraso", "nao_entregue": "Não entregue"}
    rows_t = []
    for item in temas_lista:
        t = item["tema"]
        resp = ", ".join(p["nome"].split()[0] for p in item["padrinhos"][:4])
        if len(item["padrinhos"]) > 4:
            resp += f" +{len(item['padrinhos']) - 4}"
        rows_t.append([t["titulo"], t["data_limite"] or "—", resp or "—",
                       _sit.get(t["situacao"] or "pendente", t["situacao"] or "—")])
    story.append(_dt(["Tema", "Prazo", "Responsáveis", "Situação"], rows_t,
                     [W * 0.30, W * 0.14, W * 0.36, W * 0.20]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(_sh("RESULTADO FINAL — APTIDÃO ACG", HexColor('#f0fdf4'), HexColor('#166534')))
    story.append(Spacer(1, 0.2 * cm))
    resultado = Table([[
        _p(f"<b>{len(aptos)}</b><br/>Aptos", "Helvetica-Bold", 12, HexColor('#166534')),
        _p(f"<b>{len(alertas)}</b><br/>Em alerta", "Helvetica-Bold", 12, HexColor('#b45309')),
        _p(f"<b>{len(inaptos_amarelo)}</b><br/>Inaptos", "Helvetica-Bold", 12, HexColor('#c2410c')),
        _p(f"<b>{len(inaptos_vermelho)}</b><br/>Inaptos Graves", "Helvetica-Bold", 12, HexColor('#991b1b')),
    ]], colWidths=[W / 4] * 4)
    resultado.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  HexColor('#f0fdf4')),
        ("BACKGROUND",    (1, 0), (1, -1),  HexColor('#fffbeb')),
        ("BACKGROUND",    (2, 0), (2, -1),  HexColor('#fff7ed')),
        ("BACKGROUND",    (3, 0), (3, -1),  HexColor('#fff1f2')),
        ("BOX",           (0, 0), (0, -1),  0.8, HexColor('#bbf7d0')),
        ("BOX",           (1, 0), (1, -1),  0.8, HexColor('#fde68a')),
        ("BOX",           (2, 0), (2, -1),  0.8, HexColor('#fed7aa')),
        ("BOX",           (3, 0), (3, -1),  0.8, HexColor('#fecdd3')),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(resultado)
    story.append(Spacer(1, 0.4 * cm))
    story.append(_ft(f"Gerado pelo Padrinho Track  |  {cfg['instituicao']}  |  {cfg['programa']}  |  {hoje}"))

    doc.build(story)
    return buf.getvalue()


def gerar_pdf_inaptos_graves():
    """Relatório 3: Inaptos graves — para reportar ao professor coordenador."""
    cfg = get_config_semestre()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle
    import io
    from datetime import date as _date

    hoje = _date.today().strftime("%d/%m/%Y")
    dados = get_relatorio_geral()
    inaptos_vermelho = [d for d in dados if d["status"] == "inapto_vermelho"]

    conn = get_conn()
    rows_v = []
    for d in inaptos_vermelho:
        adv = conn.execute("""
            SELECT motivo, data FROM advertencias
            WHERE padrinho_id=? AND tipo='vermelho'
            ORDER BY data DESC LIMIT 1
        """, (d["padrinho"]["id"],)).fetchone()
        rows_v.append([
            d["padrinho"]["nome"],
            d["padrinho"]["matricula"],
            d["padrinho"]["email"] or "—",
            adv["motivo"] if adv else "—",
            adv["data"] if adv else "—",
        ])
    conn.close()

    DARK_RED = HexColor('#991b1b')
    RED_BG   = HexColor('#fef2f2')
    RED_BORDER = HexColor('#fecaca')
    RED_STRIPE = HexColor('#fff5f5')

    W = A4[0] - 4 * cm
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title="Inaptos Graves — Padrinho Track")

    _p, _dt, _sh, _ph, _sig, _ft = _pdf_helpers(W)

    story = []

    story.append(_ph(
        "<b>PADRINHO</b> <font color='#fca5a5'>TRACK</font>",
        f"Ocorrências Graves — {cfg['semestre']}<br/>"
        f"<font size='8'>{cfg['instituicao']}   |   {hoje}</font>",
        DARK_RED
    ))
    story.append(Spacer(1, 0.5 * cm))

    aviso = Table([[_p(
        f"Este documento lista os padrinhos com advertência grave no semestre {cfg['semestre']}, "
        f"totalizando <b>{len(inaptos_vermelho)} caso{'s' if len(inaptos_vermelho) != 1 else ''}</b>. "
        f"Esses padrinhos estão inaptos para emissão de ACG e devem ser reportados ao coordenador.",
        "Helvetica", 9, DARK_RED, 0)]], colWidths=[W])
    aviso.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), RED_BG),
        ("BOX",           (0, 0), (-1, -1), 0.8, RED_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    story.append(aviso)
    story.append(Spacer(1, 0.5 * cm))

    story.append(_dt(
        ["Nome Completo", "Matrícula", "Email", "Motivo", "Data"],
        rows_v,
        [W * 0.24, W * 0.14, W * 0.22, W * 0.29, W * 0.11],
        stripe=RED_STRIPE, border=RED_BORDER
    ))
    story.append(Spacer(1, 1.0 * cm))

    sig, sig_labels = _sig(
        f"Professor Coordenador\n{cfg['professor_coordenador']}",
        "Responsável pelo Programa\n "
    )
    story.append(sig)
    story.append(sig_labels)
    story.append(Spacer(1, 0.4 * cm))

    footer = Table([[_p(
        f"Gerado pelo Padrinho Track  |  {cfg['instituicao']}  |  {hoje}  |  CONFIDENCIAL",
        "Helvetica", 7, HexColor('#94a3b8'))]], colWidths=[W])
    footer.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0),  0.5, RED_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(footer)

    doc.build(story)
    return buf.getvalue()



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
