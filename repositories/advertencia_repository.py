from database import get_conn
from datetime import date


def listar_com_padrinho():
    """Lista advertências com o nome do padrinho."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*, p.nome AS padrinho_nome
        FROM advertencias a
        JOIN padrinhos p ON p.id = a.padrinho_id
        ORDER BY a.data DESC
    """).fetchall()
    conn.close()
    return rows


def buscar_padrinho_id(advertencia_id):
    """Busca o padrinho associado a uma advertência."""
    conn = get_conn()
    row = conn.execute("SELECT padrinho_id FROM advertencias WHERE id=?", (advertencia_id,)).fetchone()
    conn.close()
    return row["padrinho_id"] if row else None


def listar_vermelhas_recentes():
    """Lista advertências graves da mais recente para a mais antiga."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT padrinho_id, motivo, data FROM advertencias WHERE tipo='vermelho' ORDER BY data DESC"
    ).fetchall()
    conn.close()
    return rows


def contar_por_tipo_padrinho(padrinho_id):
    """Conta advertências de um padrinho agrupadas por tipo."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT tipo, COUNT(*) AS cnt FROM advertencias WHERE padrinho_id = ? GROUP BY tipo",
        (padrinho_id,),
    ).fetchall()
    conn.close()
    return rows


def contar_por_tipo_padrinhos(padrinho_ids):
    """Conta advertências por tipo para vários padrinhos."""
    if not padrinho_ids:
        return []
    conn = get_conn()
    ph = ",".join("?" * len(padrinho_ids))
    rows = conn.execute(
        f"SELECT padrinho_id, tipo, COUNT(*) AS cnt FROM advertencias "
        f"WHERE padrinho_id IN ({ph}) GROUP BY padrinho_id, tipo",
        list(padrinho_ids),
    ).fetchall()
    conn.close()
    return rows


def listar_por_padrinho(padrinho_id):
    """Lista advertências de um padrinho."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM advertencias WHERE padrinho_id = ? ORDER BY data DESC",
        (padrinho_id,),
    ).fetchall()
    conn.close()
    return rows


def buscar_existente(padrinho_id, motivo):
    """Busca advertência já emitida para evitar duplicidade."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM advertencias WHERE padrinho_id=? AND motivo=?",
        (padrinho_id, motivo),
    ).fetchone()
    conn.close()
    return row


def criar(padrinho_id, tipo, origem, motivo, data=None):
    """Cria uma advertência."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
        VALUES (?, ?, ?, ?, ?)
    """, (padrinho_id, tipo, origem, motivo, data or date.today().isoformat()))
    conn.commit()
    conn.close()


def criar_varias(registros):
    """Cria várias advertências em uma transação."""
    conn = get_conn()
    for padrinho_id, tipo, origem, motivo, data_value in registros:
        conn.execute("""
            INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
            VALUES (?, ?, ?, ?, ?)
        """, (padrinho_id, tipo, origem, motivo, data_value))
    conn.commit()
    conn.close()


def excluir(advertencia_id):
    """Remove uma advertência."""
    conn = get_conn()
    conn.execute("DELETE FROM advertencias WHERE id=?", (advertencia_id,))
    conn.commit()
    conn.close()
