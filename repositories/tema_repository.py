from database import get_conn
from collections import defaultdict


def buscar_proximo_pendente():
    """Busca o próximo tema pendente pelo prazo."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM temas WHERE situacao = 'pendente' ORDER BY data_limite ASC LIMIT 1"
    ).fetchone()
    conn.close()
    return row


def buscar_por_id(tema_id):
    """Busca um tema pelo ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
    conn.close()
    return row


def listar_com_responsaveis():
    """Lista temas com seus padrinhos responsáveis."""
    conn = get_conn()
    temas = conn.execute("SELECT * FROM temas ORDER BY data_limite ASC").fetchall()
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


def listar_id_titulo():
    """Lista IDs e títulos dos temas."""
    conn = get_conn()
    rows = conn.execute("SELECT id, titulo FROM temas").fetchall()
    conn.close()
    return rows


def listar_padrinho_ids(tema_id):
    """Lista IDs dos padrinhos responsáveis por um tema."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT padrinho_id FROM tema_padrinhos WHERE tema_id = ?", (tema_id,)
    ).fetchall()
    conn.close()
    return [r["padrinho_id"] for r in rows]


def listar_historico_padrinho(padrinho_id):
    """Lista temas vinculados a um padrinho."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.titulo, t.data_limite, t.data_entrega, t.situacao
        FROM temas t
        JOIN tema_padrinhos tp ON tp.tema_id = t.id
        WHERE tp.padrinho_id = ?
        ORDER BY t.data_limite DESC
    """, (padrinho_id,)).fetchall()
    conn.close()
    return rows


def criar(titulo, data_aviso, data_limite, padrinho_ids):
    """Cria um tema e vincula responsáveis."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO temas (titulo, data_aviso, data_limite) VALUES (?, ?, ?)",
        (titulo, data_aviso, data_limite),
    )
    tema_id = cur.lastrowid
    for pid in padrinho_ids:
        conn.execute(
            "INSERT INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
            (tema_id, pid),
        )
    conn.commit()
    conn.close()
    return tema_id


def atualizar_entrega(tema_id, data_entrega, situacao):
    """Atualiza entrega e situação de um tema."""
    conn = get_conn()
    conn.execute(
        "UPDATE temas SET data_entrega = ?, situacao = ? WHERE id = ?",
        (data_entrega, situacao, tema_id),
    )
    conn.commit()
    conn.close()


def marcar_situacao(tema_id, situacao):
    """Atualiza somente a situação de um tema."""
    conn = get_conn()
    conn.execute("UPDATE temas SET situacao = ? WHERE id = ?", (situacao, tema_id))
    conn.commit()
    conn.close()


def excluir(tema_id):
    """Remove um tema e seus vínculos."""
    conn = get_conn()
    conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
    conn.execute("DELETE FROM temas WHERE id=?", (tema_id,))
    conn.commit()
    conn.close()


def atualizar(tema_id, titulo, data_aviso, data_limite, padrinho_ids):
    """Atualiza tema e substitui responsáveis."""
    conn = get_conn()
    conn.execute(
        "UPDATE temas SET titulo=?, data_aviso=?, data_limite=? WHERE id=?",
        (titulo, data_aviso, data_limite, tema_id),
    )
    conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
    for pid in padrinho_ids:
        conn.execute(
            "INSERT INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
            (tema_id, pid),
        )
    conn.commit()
    conn.close()


def substituir_responsaveis(tema_id, padrinho_ids):
    """Substitui todos os responsáveis vinculados a um tema."""
    conn = get_conn()
    conn.execute("DELETE FROM tema_padrinhos WHERE tema_id=?", (tema_id,))
    for padrinho_id in padrinho_ids:
        conn.execute(
            "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
            (tema_id, padrinho_id),
        )
    conn.commit()
    conn.close()
