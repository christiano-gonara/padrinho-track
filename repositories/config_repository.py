from database import get_conn


def obter(chave, padrao=None):
    """Busca uma configuração simples pela chave."""
    conn = get_conn()
    row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return row["valor"] if row else padrao


def salvar(chave, valor):
    """Cria ou atualiza uma configuração simples."""
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()
