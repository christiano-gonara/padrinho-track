from database import get_conn
from collections import defaultdict


def contar_matches():
    """Conta vínculos padrinho-calouro registrados."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    conn.close()
    return total


def substituir_matches(resultado):
    """Apaga matches atuais e grava o resultado do algoritmo."""
    conn = get_conn()
    conn.execute("DELETE FROM matches")
    for grupo in resultado["resultado"]:
        for item in grupo["calouros"]:
            conn.execute(
                "INSERT OR IGNORE INTO matches (padrinho_id, calouro_id) VALUES (?, ?)",
                (grupo["padrinho"]["id"], item["calouro"]["id"]),
            )
    conn.commit()
    conn.close()


def apagar_todos():
    """Remove todos os matches cadastrados."""
    conn = get_conn()
    conn.execute("DELETE FROM matches")
    conn.commit()
    conn.close()


def listar_contatos():
    """Lista dados de contato resultantes do match."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.nome as padrinho_nome, p.turno, c.nome as calouro_nome, c.telefone
        FROM matches m
        JOIN padrinhos p ON p.id = m.padrinho_id
        JOIN calouros c ON c.id = m.calouro_id
        ORDER BY p.nome, c.nome
    """).fetchall()
    conn.close()
    return rows


def listar_calouros_por_padrinho_completo():
    """Lista padrinhos ativos com os calouros vinculados a cada um."""
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
