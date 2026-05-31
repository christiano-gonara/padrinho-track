"""Testes de entrega, atraso e responsáveis de temas."""

import pytest
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import (
    calcular_status,
    registrar_entrega_tema,
    marcar_tema_nao_entregue,
    registrar_tema,
    cadastrar_padrinho,
)


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    yield


def _padrinho(nome="Padrinho Teste", matricula="999001"):
    cadastrar_padrinho(nome, matricula, f"{matricula}@exemplo.com", "31900000000", "Noite")
    conn = get_conn()
    row = conn.execute("SELECT id FROM padrinhos WHERE matricula=?", (matricula,)).fetchone()
    conn.close()
    return row["id"]

def _tema(pid, data_limite="2026-05-10"):
    registrar_tema("Tema Teste", "2026-01-01", data_limite, [pid])
    conn = get_conn()
    tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
    conn.close()
    return tid


class TestRegistrarEntregaTema:

    def test_entrega_no_prazo_nao_gera_advertencia(self):
        pid = _padrinho()
        tid = _tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-10")
        assert situacao == "entregue"
        assert calcular_status(pid)["amarelos"] == 0

    def test_entrega_antes_do_prazo_nao_gera_advertencia(self):
        pid = _padrinho()
        tid = _tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-08")
        assert situacao == "entregue"
        assert calcular_status(pid)["amarelos"] == 0

    def test_entrega_com_1_dia_atraso_gera_amarelo(self):
        pid = _padrinho()
        tid = _tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-11")
        assert situacao == "atraso"
        assert calcular_status(pid)["amarelos"] == 1

    def test_entrega_com_mais_de_1_dia_gera_vermelho(self):
        pid = _padrinho()
        tid = _tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-13")
        assert situacao == "nao_entregue"
        assert calcular_status(pid)["vermelhos"] == 1

    def test_atraso_afeta_todos_do_grupo(self):
        pid1 = _padrinho("Padrinho A", "999001")
        pid2 = _padrinho("Padrinho B", "999002")
        registrar_tema("Tema Grupo", "2026-01-01", "2026-05-10", [pid1, pid2])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        registrar_entrega_tema(tid, "2026-05-11")
        assert calcular_status(pid1)["amarelos"] == 1
        assert calcular_status(pid2)["amarelos"] == 1


class TestMarcarTemaNaoEntregue:

    def test_nao_entregue_gera_vermelho(self):
        pid = _padrinho()
        tid = _tema(pid)
        marcar_tema_nao_entregue(tid)
        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"
        assert status["vermelhos"] == 1

    def test_nao_entregue_afeta_todos_do_grupo(self):
        pid1 = _padrinho("Padrinho A", "999001")
        pid2 = _padrinho("Padrinho B", "999002")
        registrar_tema("Tema Grupo NE", "2026-01-01", "2026-05-10", [pid1, pid2])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        marcar_tema_nao_entregue(tid)
        assert calcular_status(pid1)["vermelhos"] == 1
        assert calcular_status(pid2)["vermelhos"] == 1

    def test_nao_entregue_nao_afeta_padrinho_sem_tema(self):
        pid1 = _padrinho("Padrinho A", "999001")
        pid2 = _padrinho("Padrinho B", "999002")
        registrar_tema("Tema Só A", "2026-01-01", "2026-05-10", [pid1])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        marcar_tema_nao_entregue(tid)
        assert calcular_status(pid2)["vermelhos"] == 0


class TestIdempotenciaTemas:

    def test_registrar_entrega_tema_idempotente(self):
        """Registrar entrega do mesmo tema duas vezes não duplica advertências."""
        pid = _padrinho()
        tid = _tema(pid)
        registrar_entrega_tema(tid, "2026-05-11")
        registrar_entrega_tema(tid, "2026-05-11")
        assert calcular_status(pid)["amarelos"] == 1

    def test_marcar_tema_nao_entregue_idempotente(self):
        """Marcar tema não entregue duas vezes não duplica vermelho."""
        pid = _padrinho()
        tid = _tema(pid)
        marcar_tema_nao_entregue(tid)
        marcar_tema_nao_entregue(tid)
        assert calcular_status(pid)["vermelhos"] == 1
