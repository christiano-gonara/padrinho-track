"""Testes das regras de advertência e cálculo de status."""

import pytest
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import (
    calcular_status,
    emitir_advertencia_manual,
    cadastrar_padrinho,
    criar_reuniao,
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

def _inserir_advertencia(padrinho_id, tipo, origem="falta"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data) VALUES (?,?,?,?,?)",
        (padrinho_id, tipo, origem, "teste", date.today().isoformat())
    )
    conn.commit()
    conn.close()

def _criar_reunioes(n):
    for i in range(n):
        criar_reuniao(f"2026-0{i % 9 + 1}-{i // 9 * 7 + 1:02d}", f"Reunião {i + 1}", "")


# ── calcular_status ────────────────────────────────────────────────────────

class TestCalcularStatus:

    def test_sem_advertencias_retorna_apto(self):
        _criar_reunioes(2)
        pid = _padrinho()
        status = calcular_status(pid)
        assert status["status"] == "apto"
        assert status["amarelos"] == 0
        assert status["vermelhos"] == 0

    def test_um_amarelo_retorna_alerta(self):
        _criar_reunioes(2)
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid)
        assert status["status"] == "alerta"
        assert status["amarelos"] == 1

    def test_dois_amarelos_retorna_inapto_amarelo(self):
        _criar_reunioes(2)
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid)
        assert status["status"] == "inapto_amarelo"
        assert status["amarelos"] == 2

    def test_tres_amarelos_continua_inapto_amarelo(self):
        _criar_reunioes(3)
        pid = _padrinho()
        for _ in range(3):
            _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid)
        assert status["status"] == "inapto_amarelo"

    def test_um_vermelho_retorna_inapto_vermelho(self):
        _criar_reunioes(2)
        pid = _padrinho()
        _inserir_advertencia(pid, "vermelho")
        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"
        assert status["vermelhos"] == 1

    def test_vermelho_sobrepoe_amarelos(self):
        _criar_reunioes(2)
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        _inserir_advertencia(pid, "vermelho")
        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"

    def test_padrinhos_independentes(self):
        _criar_reunioes(3)
        pid1 = _padrinho("Padrinho A", "999001")
        pid2 = _padrinho("Padrinho B", "999002")
        _inserir_advertencia(pid1, "amarelo")
        _inserir_advertencia(pid1, "amarelo")
        status2 = calcular_status(pid2)
        assert status2["status"] == "apto"


# ── emitir_advertencia_manual ──────────────────────────────────────────────

class TestAdvertenciaManual:

    def test_manual_gera_vermelho(self):
        pid = _padrinho()
        emitir_advertencia_manual(pid, "Comportamento inadequado")
        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"
        assert status["vermelhos"] == 1

    def test_manual_com_amarelos_anteriores(self):
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        emitir_advertencia_manual(pid, "Comportamento inadequado")
        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"
        assert status["amarelos"] == 1
        assert status["vermelhos"] == 1


# ── calcular_status com limite configurável ───────────────────────────────

class TestCalcularStatusLimiteCustom:

    def test_apto_com_amarelo_retorna_contagem_real(self):
        """Com limite=3, 1 amarelo ainda é apto — count deve ser 1, não 0 (fix C1)."""
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid, limite=3)
        assert status["status"] == "apto"
        assert status["amarelos"] == 1

    def test_alerta_com_limite_custom(self):
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid, limite=3)
        assert status["status"] == "alerta"
        assert status["amarelos"] == 2

    def test_inapto_amarelo_com_limite_custom(self):
        pid = _padrinho()
        for _ in range(3):
            _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid, limite=3)
        assert status["status"] == "inapto_amarelo"
        assert status["amarelos"] == 3

    def test_vermelho_sobrepoe_independente_do_limite(self):
        pid = _padrinho()
        _inserir_advertencia(pid, "vermelho")
        status = calcular_status(pid, limite=10)
        assert status["status"] == "inapto_vermelho"
