from database import get_conn
from datetime import date, datetime

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

    if vermelhos >= 1:
        return {"status": "inapto_vermelho", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos >= 2:
        return {"status": "inapto_amarelo", "amarelos": amarelos, "vermelhos": vermelhos}
    if amarelos == 1:
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