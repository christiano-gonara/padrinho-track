from database import get_conn
from datetime import date, datetime

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
    conn = get_conn()
    temas = conn.execute(
        "SELECT * FROM temas ORDER BY data_limite ASC"
    ).fetchall()
    resultado = []
    for t in temas:
        padrinhos = conn.execute("""
            SELECT p.id, p.nome FROM padrinhos p
            JOIN tema_padrinhos tp ON tp.padrinho_id = p.id
            WHERE tp.tema_id = ?
            ORDER BY p.nome
        """, (t["id"],)).fetchall()
        resultado.append({"tema": t, "padrinhos": padrinhos})
    conn.close()
    return resultado

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

def registrar_entrega_tema(tema_id, data_entrega_str):
    conn = get_conn()
    tema = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()

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
        padrinhos = conn.execute(
            "SELECT padrinho_id FROM tema_padrinhos WHERE tema_id = ?", (tema_id,)
        ).fetchall()
        for p in padrinhos:
            conn.execute("""
                INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
                VALUES (?, 'amarelo', 'atraso_tema', ?, ?)
            """, (p["padrinho_id"], f"Entrega com atraso: {tema['titulo']}", date.today().isoformat()))

    elif situacao == "nao_entregue":
        padrinhos = conn.execute(
            "SELECT padrinho_id FROM tema_padrinhos WHERE tema_id = ?", (tema_id,)
        ).fetchall()
        for p in padrinhos:
            conn.execute("""
                INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
                VALUES (?, 'vermelho', 'nao_entrega', ?, ?)
            """, (p["padrinho_id"], f"Não entregou: {tema['titulo']}", date.today().isoformat()))

    conn.commit()
    conn.close()
    return situacao

def marcar_tema_nao_entregue(tema_id):
    conn = get_conn()
    tema = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
    conn.execute(
        "UPDATE temas SET situacao = 'nao_entregue' WHERE id = ?", (tema_id,)
    )
    padrinhos = conn.execute(
        "SELECT padrinho_id FROM tema_padrinhos WHERE tema_id = ?", (tema_id,)
    ).fetchall()
    for p in padrinhos:
        conn.execute("""
            INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
            VALUES (?, 'vermelho', 'nao_entrega', ?, ?)
        """, (p["padrinho_id"], f"Não entregou: {tema['titulo']}", date.today().isoformat()))
    conn.commit()
    conn.close()

def emitir_advertencias_falta(reuniao_id):
    conn = get_conn()
    ausentes = conn.execute("""
        SELECT padrinho_id FROM presencas
        WHERE reuniao_id = ? AND presente = 0 AND justificada = 0
    """, (reuniao_id,)).fetchall()
    for row in ausentes:
        conn.execute("""
            INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
            VALUES (?, 'amarelo', 'falta', 'Falta sem justificativa', ?)
        """, (row["padrinho_id"], date.today().isoformat()))
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

def calcular_status(padrinho_id):
    conn = get_conn()
    amarelos = conn.execute(
        "SELECT COUNT(*) FROM advertencias WHERE padrinho_id = ? AND tipo = 'amarelo'",
        (padrinho_id,)
    ).fetchone()[0]
    vermelhos = conn.execute(
        "SELECT COUNT(*) FROM advertencias WHERE padrinho_id = ? AND tipo = 'vermelho'",
        (padrinho_id,)
    ).fetchone()[0]
    conn.close()

    limite = int(get_config("limite_amarelos", "2"))

    if vermelhos >= 1:
        return {"status": "inapto_vermelho", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos >= limite:
        return {"status": "inapto_amarelo", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos == limite - 1:
        return {"status": "alerta", "amarelos": amarelos, "vermelhos": vermelhos}
    return {"status": "apto", "amarelos": 0, "vermelhos": 0}

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
    relatorio = []
    for p in padrinhos:
        status   = calcular_status(p["id"])
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
    import pandas as pd
    dados = get_relatorio_geral()
    rows = []
    for d in dados:
        rows.append({
            "Nome":            d["padrinho"]["nome"],
            "Matricula":       d["padrinho"]["matricula"],
            "Email":           d["padrinho"]["email"] or "",
            "Telefone":        d["padrinho"]["telefone"] or "",
            "Turno":           d["padrinho"]["turno"] or "",
            "Reunioes":        d["total_reunioes"],
            "Presencas":       d["total_presentes"],
            "Amarelos":        d["amarelos"],
            "Vermelhos":       d["vermelhos"],
            "Status":          d["status"],
        })
    df = pd.DataFrame(rows)
    df.to_csv(caminho, index=False, encoding="utf-8-sig")
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
    conn = get_conn()
    padrinhos = conn.execute(
        "SELECT * FROM padrinhos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    resultado = []
    for p in padrinhos:
        calouros = conn.execute("""
            SELECT c.id, c.nome, c.telefone
            FROM calouros c
            JOIN matches m ON m.calouro_id = c.id
            WHERE m.padrinho_id = ?
            ORDER BY c.nome
        """, (p["id"],)).fetchall()
        resultado.append({"padrinho": p, "calouros": calouros})
    conn.close()
    return resultado

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

def get_relatorio_aptos():
    padrinhos = get_todos_padrinhos()
    resultado = []
    for p in padrinhos:
        status = calcular_status(p["id"])
        if status["status"] == "apto":
            historico = get_historico_padrinho(p["id"])
            resultado.append({
                "padrinho": p,
                "total_reunioes": len(historico["presencas"]),
                "total_presentes": sum(1 for pr in historico["presencas"] if pr["presente"]),
                "amarelos": status["amarelos"],
                "vermelhos": status["vermelhos"],
            })
    return resultado

def get_relatorio_vermelhos():
    padrinhos = get_todos_padrinhos()
    resultado = []
    for p in padrinhos:
        status = calcular_status(p["id"])
        if status["status"] == "inapto_vermelho":
            advertencias = get_advertencias_padrinho(p["id"])
            vermelhos = [a for a in advertencias if a["tipo"] == "vermelho"]
            resultado.append({
                "padrinho": p,
                "vermelhos": vermelhos,
                "amarelos": status["amarelos"],
                "total_vermelhos": status["vermelhos"],
            })
    return resultado

def exportar_aptos_csv(caminho="instance/relatorio_aptos.csv"):
    import pandas as pd
    dados = get_relatorio_aptos()
    rows = [{"Nome": d["padrinho"]["nome"], "Matricula": d["padrinho"]["matricula"],
             "Email": d["padrinho"]["email"] or "", "Turno": d["padrinho"]["turno"] or "",
             "Reunioes": d["total_reunioes"], "Presencas": d["total_presentes"]} for d in dados]
    pd.DataFrame(rows).to_csv(caminho, index=False, encoding="utf-8-sig")
    return caminho

def exportar_vermelhos_csv(caminho="instance/relatorio_vermelhos.csv"):
    import pandas as pd
    dados = get_relatorio_vermelhos()
    rows = []
    for d in dados:
        for a in d["vermelhos"]:
            rows.append({
                "Nome": d["padrinho"]["nome"],
                "Matricula": d["padrinho"]["matricula"],
                "Email": d["padrinho"]["email"] or "",
                "Origem": a["origem"],
                "Motivo": a["motivo"] or "",
                "Data": a["data"],
            })
    pd.DataFrame(rows).to_csv(caminho, index=False, encoding="utf-8-sig")
    return caminho

def gerar_pdf_acg():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from datetime import date
    import io

    dados = get_relatorio_geral()
    hoje = date.today().strftime("%d/%m/%Y")

    aptos            = [d for d in dados if d["status"] == "apto"]
    inaptos_amarelo  = [d for d in dados if d["status"] == "inapto_amarelo"]
    inaptos_vermelho = [d for d in dados if d["status"] == "inapto_vermelho"]

    conn = get_conn()
    vermelhos_rows_data = []
    for d in inaptos_vermelho:
        adv = conn.execute("""
            SELECT motivo FROM advertencias
            WHERE padrinho_id = ? AND tipo = 'vermelho'
            ORDER BY data DESC LIMIT 1
        """, (d["padrinho"]["id"],)).fetchone()
        vermelhos_rows_data.append({
            "padrinho": d["padrinho"],
            "motivo": adv["motivo"] if adv else "-",
        })
    conn.close()

    # Palette
    INDIGO     = HexColor('#6366f1')
    VERDE_BG   = HexColor('#dcfce7')
    LARANJA_BG = HexColor('#ffedd5')
    VERM_BG    = HexColor('#fee2e2')
    SLATE_BG   = HexColor('#f8fafc')
    STRIPE     = HexColor('#f1f5f9')
    BORDER     = HexColor('#e2e8f0')
    SLATE_TXT  = HexColor('#64748b')
    BODY_TXT   = HexColor('#1e293b')

    W = A4[0] - 4 * cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Relatorio de Aptidao ACG - Padrinho Track",
    )

    def _p(text, font="Helvetica", size=9, color=BODY_TXT, align=TA_CENTER):
        return Paragraph(
            f'<font name="{font}" size="{size}">{text}</font>',
            ParagraphStyle("_", fontName=font, fontSize=size, textColor=color, alignment=align),
        )

    def _section_header(label, bg, text_color):
        t = Table([[_p(label, "Helvetica-Bold", 10, text_color, TA_CENTER)]],
                  colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BORDER),
        ]))
        return t

    def _data_table(headers, rows, col_widths):
        from reportlab.lib.enums import TA_LEFT
        cell_style = ParagraphStyle(
            "_cell", fontName="Helvetica", fontSize=10, textColor=BODY_TXT, alignment=TA_LEFT
        )

        def _cell(val):
            return Paragraph(str(val) if val else "-", cell_style)

        header_cells = [_p(h, "Helvetica-Bold", 7, SLATE_TXT) for h in headers]
        raw_body = rows if rows else [["Nenhum registro."] + [""] * (len(headers) - 1)]
        body = [[_cell(v) for v in row] for row in raw_body]
        data = [header_cells] + body
        style = [
            ("BACKGROUND",    (0, 0), (-1, 0),  SLATE_BG),
            ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BORDER),
            ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        for i in range(2, len(data), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), STRIPE))
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle(style))
        return t

    story = []

    # Cabecalho
    header = Table(
        [[
            _p("Padrinho Track - Relatorio de Aptidao ACG",
               "Helvetica-Bold", 14, white, TA_CENTER),
            _p(f"Semestre 2026/1  |  Gerado em {hoje}",
               "Helvetica", 8, white, TA_RIGHT),
        ]],
        colWidths=[W * 0.65, W * 0.35],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INDIGO),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (0, -1),  16),
        ("RIGHTPADDING",  (-1, 0), (-1, -1), 16),
    ]))
    story.append(header)
    story.append(Spacer(1, 0.5 * cm))

    # Cards de resumo
    summary = Table(
        [[
            _p(f"<b>{len(aptos)}</b>  APTOS",
               "Helvetica-Bold", 11, HexColor('#166534')),
            _p(f"<b>{len(inaptos_amarelo)}</b>  INAPTOS",
               "Helvetica-Bold", 11, HexColor('#c2410c')),
            _p(f"<b>{len(inaptos_vermelho)}</b>  INAPTOS GRAVES",
               "Helvetica-Bold", 11, HexColor('#991B1B')),
        ]],
        colWidths=[W / 3, W / 3, W / 3],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  HexColor('#f0fdf4')),
        ("BACKGROUND",    (1, 0), (1, -1),  HexColor('#fff7ed')),
        ("BACKGROUND",    (2, 0), (2, -1),  HexColor('#fff1f2')),
        ("BOX",           (0, 0), (0, -1),  0.8, HexColor('#bbf7d0')),
        ("BOX",           (1, 0), (1, -1),  0.8, HexColor('#fed7aa')),
        ("BOX",           (2, 0), (2, -1),  0.8, HexColor('#fecdd3')),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary)
    story.append(Spacer(1, 0.6 * cm))

    # Secao APTOS
    story.append(_section_header(f"APTOS  ({len(aptos)})", VERDE_BG, HexColor('#166534')))
    story.append(Spacer(1, 0.15 * cm))
    rows_a = [[d["padrinho"]["nome"], d["padrinho"]["matricula"], d["padrinho"]["turno"] or "-"]
              for d in aptos]
    story.append(_data_table(["Nome", "Matricula", "Turno"], rows_a,
                             [W * 0.55, W * 0.25, W * 0.20]))
    story.append(Spacer(1, 0.5 * cm))

    # Secao INAPTOS AMARELO
    story.append(_section_header(
        f"INAPTOS  ({len(inaptos_amarelo)})",
        LARANJA_BG, HexColor('#c2410c')))
    story.append(Spacer(1, 0.15 * cm))
    rows_am = [[d["padrinho"]["nome"], d["padrinho"]["matricula"],
                f"{d['amarelos']} amarelo{'s' if d['amarelos'] != 1 else ''}"]
               for d in inaptos_amarelo]
    story.append(_data_table(["Nome", "Matricula", "Amarelos"], rows_am,
                             [W * 0.55, W * 0.25, W * 0.20]))
    story.append(Spacer(1, 0.5 * cm))

    # Secao INAPTOS VERMELHO
    story.append(_section_header(
        f"INAPTOS GRAVES  ({len(inaptos_vermelho)})",
        VERM_BG, HexColor('#991B1B')))
    story.append(Spacer(1, 0.15 * cm))
    rows_v = [[r["padrinho"]["nome"], r["padrinho"]["matricula"], r["motivo"] or "-"]
              for r in vermelhos_rows_data]
    story.append(_data_table(["Nome", "Matricula", "Motivo"], rows_v,
                             [W * 0.35, W * 0.20, W * 0.45]))
    story.append(Spacer(1, 0.8 * cm))

    # Rodape
    footer = Table(
        [[_p(f"Gerado automaticamente pelo Padrinho Track  |  PUC Minas  |  "
             f"Eng. de Software  |  2026/1  |  {hoje}",
             "Helvetica", 7, HexColor('#94a3b8'))]],
        colWidths=[W],
    )
    footer.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0),  0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(footer)

    doc.build(story)
    return buf.getvalue()


def importar_presencas_csv(caminho_csv, reuniao_id):
    import pandas as pd

    df = pd.read_csv(caminho_csv)
    df.columns = df.columns.str.strip()

    # Detecta as colunas automaticamente
    col_matricula = None
    col_situacao = None
    for col in df.columns:
        col_lower = col.lower()
        if "matrícula" in col_lower or "matricula" in col_lower:
            col_matricula = col
        if "situação" in col_lower or "situacao" in col_lower or "situac" in col_lower:
            col_situacao = col

    if not col_matricula:
        return {"erro": "Coluna de matrícula não encontrada no CSV."}

    conn = get_conn()
    processados = 0
    nao_encontrados = []

    for _, row in df.iterrows():
        matricula = str(row[col_matricula]).strip().replace(".0", "")
        padrinho = conn.execute(
            "SELECT id FROM padrinhos WHERE matricula = ?", (matricula,)
        ).fetchone()

        if not padrinho:
            nao_encontrados.append(matricula)
            continue

        presente = 1
        justificada = 0

        if col_situacao:
            situacao = str(row[col_situacao]).strip().lower()
            if "justificativa" in situacao or "ausente" in situacao:
                presente = 0
                justificada = 1

        conn.execute("""
            INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(reuniao_id, padrinho_id)
            DO UPDATE SET presente=excluded.presente, justificada=excluded.justificada
        """, (reuniao_id, padrinho["id"], presente, justificada))
        processados += 1

    # Emite amarelos para quem não apareceu no CSV e não tem presença registrada
    todos = conn.execute(
        "SELECT id FROM padrinhos WHERE ativo=1"
    ).fetchall()
    for p in todos:
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
