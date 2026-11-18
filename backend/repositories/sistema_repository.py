from datetime import datetime

from backend.database import get_conn


def registrar_log(acao, descricao, ip=None):
    """Registra uma ação operacional do sistema."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO logs (acao, descricao, data, ip) VALUES (?, ?, ?, ?)",
        (acao, descricao, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip),
    )
    conn.commit()
    conn.close()


def obter_config(chave, padrao=None):
    """Busca uma configuração simples pela chave."""
    conn = get_conn()
    row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return row["valor"] if row else padrao


def salvar_config(chave, valor):
    """Cria ou atualiza uma configuração simples."""
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()
