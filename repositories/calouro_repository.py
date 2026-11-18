from database import get_conn


def contar_todos():
    """Conta todos os calouros cadastrados."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    conn.close()
    return total


def obter_resumo_demografico():
    """Busca totais demográficos usados nos relatórios."""
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(bolsista) AS bol, SUM(cidade_bh) AS bh, SUM(trabalha) AS trab FROM calouros"
    ).fetchone()
    conn.close()
    return row


def contar_por_turno():
    """Conta calouros agrupados por turno."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT turno, COUNT(*) AS qtd FROM calouros WHERE turno IS NOT NULL AND turno != '' GROUP BY turno ORDER BY turno"
    ).fetchall()
    conn.close()
    return rows


def listar_nomes():
    """Lista nomes de calouros cadastrados."""
    conn = get_conn()
    rows = conn.execute("SELECT nome FROM calouros").fetchall()
    conn.close()
    return rows
