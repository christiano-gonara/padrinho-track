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

def emitir_advertencia_manual(padrinho_id, motivo):
    conn = get_conn()
    conn.execute("""
        INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
        VALUES (?, 'vermelho', 'manual', ?, ?)
    """, (padrinho_id, motivo, date.today().isoformat()))
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
        limite = int(get_config("limite_amarelos", "2"))

    if vermelhos >= 1:
        return {"status": "inapto_vermelho", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos >= limite:
        return {"status": "inapto_amarelo", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos == limite - 1:
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

def get_relatorio_geral():
    padrinhos = get_todos_padrinhos()
    limite = int(get_config("limite_amarelos", "2"))
    relatorio = []
    for p in padrinhos:
        status   = calcular_status(p["id"], limite)
        historico = get_historico_padrinho(p["id"])
        total_reunioes  = len(historico["presencas"])
        total_presentes = sum(1 for pr in historico["presencas"] if pr["presente"])
        relatorio.append({
            "padrinho":        p,
            "status":          status["status"],
            "amarelos":        status["amarelos"],
            "vermelhos":       status["vermelhos"],
            "total_reunioes":  total_reunioes,
            "total_presentes": total_presentes,
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

def get_calouros_por_padrinho(padrinho_id):
    conn = get_conn()
    calouros = conn.execute("""
        SELECT c.id, c.nome, c.telefone
        FROM calouros c
        JOIN matches m ON m.calouro_id = c.id
        WHERE m.padrinho_id = ?
        ORDER BY c.nome
    """, (padrinho_id,)).fetchall()
    conn.close()
    return calouros

def get_todos_matches():
    conn = get_conn()
    resultado = conn.execute("""
        SELECT p.id AS padrinho_id, p.nome AS padrinho_nome,
               p.turno, COUNT(m.calouro_id) AS total_calouros
        FROM padrinhos p
        LEFT JOIN matches m ON m.padrinho_id = p.id
        WHERE p.ativo = 1
        GROUP BY p.id
        ORDER BY p.nome
    """).fetchall()
    conn.close()
    return resultado

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

def editar_padrinho(padrinho_id, nome, matricula, email, telefone, turno):
    conn = get_conn()
    conn.execute("""
        UPDATE padrinhos SET nome=?, matricula=?, email=?, telefone=?, turno=?
        WHERE id=?
    """, (nome, matricula, email, telefone, turno, padrinho_id))
    conn.commit()
    conn.close()

def excluir_padrinho(padrinho_id):
    conn = get_conn()
    conn.execute("UPDATE padrinhos SET ativo=0 WHERE id=?", (padrinho_id,))
    conn.commit()
    conn.close()

def excluir_advertencia(advertencia_id):
    conn = get_conn()
    conn.execute("DELETE FROM advertencias WHERE id=?", (advertencia_id,))
    conn.commit()
    conn.close()

def editar_presenca(reuniao_id, padrinho_id, presente, justificada):
    conn = get_conn()
    conn.execute("""
        UPDATE presencas SET presente=?, justificada=?
        WHERE reuniao_id=? AND padrinho_id=?
    """, (presente, justificada, reuniao_id, padrinho_id))
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
