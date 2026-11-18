from database import get_conn


def listar_todas_desc():
    """Lista reuniões da mais recente para a mais antiga."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM reunioes ORDER BY data DESC").fetchall()
    conn.close()
    return rows


def listar_todas_asc():
    """Lista reuniões da mais antiga para a mais recente."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM reunioes ORDER BY data ASC").fetchall()
    conn.close()
    return rows


def buscar_ultima():
    """Busca a última reunião registrada."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM reunioes ORDER BY data DESC LIMIT 1").fetchone()
    conn.close()
    return row


def buscar_por_id(reuniao_id):
    """Busca uma reunião pelo ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM reunioes WHERE id=?", (reuniao_id,)).fetchone()
    conn.close()
    return row


def contar_todas():
    """Conta reuniões cadastradas."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM reunioes").fetchone()[0]
    conn.close()
    return total


def contar_presencas_por_reuniao():
    """Conta presentes e total lançado em cada reunião."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT reuniao_id,
               SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END) AS presentes,
               COUNT(*) AS total
        FROM presencas GROUP BY reuniao_id
    """).fetchall()
    conn.close()
    return rows


def salvar_presenca(reuniao_id, padrinho_id, presente, justificada):
    """Salva uma presença individual com upsert."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(reuniao_id, padrinho_id)
        DO UPDATE SET presente = excluded.presente, justificada = excluded.justificada
    """, (reuniao_id, padrinho_id, presente, justificada))
    conn.commit()
    conn.close()


def salvar_presencas_em_lote(registros):
    """Salva várias presenças em uma única transação."""
    conn = get_conn()
    for reuniao_id, padrinho_id, presente, justificada in registros:
        conn.execute("""
            INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(reuniao_id, padrinho_id)
            DO UPDATE SET presente = excluded.presente, justificada = excluded.justificada
        """, (reuniao_id, padrinho_id, presente, justificada))
    conn.commit()
    conn.close()


def criar(data, tema, descricao):
    """Cria uma reunião."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO reunioes (data, tema, descricao) VALUES (?, ?, ?)",
        (data, tema, descricao),
    )
    conn.commit()
    conn.close()


def excluir(reuniao_id):
    """Remove uma reunião e suas presenças."""
    conn = get_conn()
    conn.execute("DELETE FROM presencas WHERE reuniao_id=?", (reuniao_id,))
    conn.execute("DELETE FROM reunioes WHERE id=?", (reuniao_id,))
    conn.commit()
    conn.close()


def atualizar(reuniao_id, data, tema, descricao):
    """Atualiza dados básicos de uma reunião."""
    conn = get_conn()
    conn.execute(
        "UPDATE reunioes SET data=?, tema=?, descricao=? WHERE id=?",
        (data, tema, descricao, reuniao_id),
    )
    conn.commit()
    conn.close()
