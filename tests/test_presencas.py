"""Testes de lançamento de presenças e advertências por falta."""

import pytest
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import (
    calcular_status,
    emitir_advertencias_falta,
    cadastrar_padrinho,
    criar_reuniao,
    lancar_presenca,
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

def _criar_reuniao():
    criar_reuniao("2026-05-01", "Teste", "")
    conn = get_conn()
    rid = conn.execute("SELECT id FROM reunioes ORDER BY id DESC LIMIT 1").fetchone()["id"]
    conn.close()
    return rid


class TestEmitirAdvertenciasFalta:

    def test_falta_sem_justificativa_gera_amarelo(self):
        pid = _padrinho()
        rid = _criar_reuniao()
        lancar_presenca(rid, pid, presente=0, justificada=0)
        emitir_advertencias_falta(rid)
        assert calcular_status(pid)["amarelos"] == 1

    def test_presenca_nao_gera_advertencia(self):
        pid = _padrinho()
        rid = _criar_reuniao()
        lancar_presenca(rid, pid, presente=1, justificada=0)
        emitir_advertencias_falta(rid)
        assert calcular_status(pid)["amarelos"] == 0

    def test_falta_justificada_nao_gera_advertencia(self):
        pid = _padrinho()
        rid = _criar_reuniao()
        lancar_presenca(rid, pid, presente=0, justificada=1)
        emitir_advertencias_falta(rid)
        assert calcular_status(pid)["amarelos"] == 0

    def test_duas_faltas_geram_dois_amarelos(self):
        pid = _padrinho()
        criar_reuniao("2026-05-01", "R1", "")
        criar_reuniao("2026-05-08", "R2", "")
        conn = get_conn()
        reunioes = conn.execute("SELECT id FROM reunioes ORDER BY id DESC LIMIT 2").fetchall()
        conn.close()
        for r in reunioes:
            lancar_presenca(r["id"], pid, presente=0, justificada=0)
            emitir_advertencias_falta(r["id"])
        assert calcular_status(pid)["amarelos"] == 2
        assert calcular_status(pid)["status"] == "inapto_amarelo"


class TestIdempotenciaPresencas:

    def test_emitir_advertencias_falta_idempotente(self):
        """Chamar emitir_advertencias_falta duas vezes para a mesma reunião não duplica amarelos."""
        pid = _padrinho()
        rid = _criar_reuniao()
        lancar_presenca(rid, pid, presente=0, justificada=0)
        emitir_advertencias_falta(rid)
        emitir_advertencias_falta(rid)
        assert calcular_status(pid)["amarelos"] == 1

    def test_emitir_advertencias_falta_duas_reunioes_distintas(self):
        """Faltas em duas reuniões diferentes geram dois amarelos mesmo chamado em sequência."""
        pid = _padrinho()
        criar_reuniao("2026-05-01", "R1", "")
        criar_reuniao("2026-05-08", "R2", "")
        conn = get_conn()
        r1, r2 = conn.execute("SELECT id FROM reunioes ORDER BY id ASC LIMIT 2").fetchall()
        conn.close()
        lancar_presenca(r1["id"], pid, presente=0, justificada=0)
        emitir_advertencias_falta(r1["id"])
        lancar_presenca(r2["id"], pid, presente=0, justificada=0)
        emitir_advertencias_falta(r2["id"])
        assert calcular_status(pid)["amarelos"] == 2
