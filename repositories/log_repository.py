from datetime import datetime

from database import get_conn


def registrar(acao, descricao, ip=None):
    """Registra uma ação operacional do sistema."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO logs (acao, descricao, data, ip) VALUES (?, ?, ?, ?)",
        (acao, descricao, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip),
    )
    conn.commit()
    conn.close()
