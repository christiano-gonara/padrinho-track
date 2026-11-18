from database import get_conn


def listar_por_reuniao(reuniao_id):
    """Lista padrinhos ativos com presença/justificativa de uma reunião."""
    conn = get_conn()
    rows = conn.execute("""
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
    return rows


def listar_historico_padrinho(padrinho_id):
    """Lista presenças lançadas de um padrinho."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.data, r.tema, pr.presente, pr.justificada
        FROM presencas pr
        JOIN reunioes r ON r.id = pr.reuniao_id
        WHERE pr.padrinho_id = ?
        ORDER BY r.data DESC
    """, (padrinho_id,)).fetchall()
    conn.close()
    return rows


def contar_por_padrinhos(padrinho_ids):
    """Conta presenças agrupadas por padrinho para o relatório geral."""
    if not padrinho_ids:
        return []
    conn = get_conn()
    ph = ",".join("?" * len(padrinho_ids))
    rows = conn.execute(
        f"SELECT padrinho_id, COUNT(*) AS total, SUM(presente) AS presentes "
        f"FROM presencas WHERE padrinho_id IN ({ph}) GROUP BY padrinho_id",
        padrinho_ids,
    ).fetchall()
    conn.close()
    return rows


def listar_ausentes_sem_justificativa(reuniao_id):
    """Lista padrinhos ausentes sem justificativa em uma reunião."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT padrinho_id FROM presencas
        WHERE reuniao_id = ? AND presente = 0 AND justificada = 0
    """, (reuniao_id,)).fetchall()
    conn.close()
    return rows
