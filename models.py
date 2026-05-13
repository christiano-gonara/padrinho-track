from database import get_conn
from datetime import date

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

def cadastrar_padrinho(nome, matricula, email):
    conn = get_conn()
    conn.execute(
        "INSERT INTO padrinhos (nome, matricula, email) VALUES (?, ?, ?)",
        (nome, matricula, email)
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

def registrar_tema(titulo, data_limite, padrinho_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO temas (titulo, data_limite, padrinho_id) VALUES (?, ?, ?)",
        (titulo, data_limite, padrinho_id)
    )
    conn.commit()
    conn.close()

def marcar_tema_entregue(tema_id):
    conn = get_conn()
    conn.execute(
        "UPDATE temas SET entregue = 1, data_entrega = ? WHERE id = ?",
        (date.today().isoformat(), tema_id)
    )
    conn.commit()
    conn.close()

def marcar_tema_nao_entregue(tema_id):
    conn = get_conn()
    tema = conn.execute(
        "SELECT * FROM temas WHERE id = ?", (tema_id,)
    ).fetchone()
    conn.execute(
        "UPDATE temas SET entregue = 0 WHERE id = ?", (tema_id,)
    )
    conn.execute("""
        INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
        VALUES (?, 'vermelho', 'nao_entrega', ?, ?)
    """, (tema["padrinho_id"], f"Não entregou: {tema['titulo']}", date.today().isoformat()))
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
    temas = conn.execute(
        "SELECT * FROM temas WHERE padrinho_id = ? ORDER BY data_limite DESC",
        (padrinho_id,)
    ).fetchall()
    conn.close()
    return {"presencas": presencas, "temas": temas}

def get_relatorio_geral():
    padrinhos = get_todos_padrinhos()
    relatorio = []
    for p in padrinhos:
        status = calcular_status(p["id"])
        historico = get_historico_padrinho(p["id"])
        total_reunioes = len(historico["presencas"])
        total_presentes = sum(1 for pr in historico["presencas"] if pr["presente"])
        relatorio.append({
            "padrinho": p,
            "status": status["status"],
            "amarelos": status["amarelos"],
            "vermelhos": status["vermelhos"],
            "total_reunioes": total_reunioes,
            "total_presentes": total_presentes,
        })
    return relatorio