"""Testes de funções gerais de models.py (configuração, cadastro)."""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import get_config, set_config, cadastrar_padrinho, get_todos_padrinhos, get_padrinho


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    yield


class TestConfig:

    def test_set_get_config(self):
        set_config("chave_teste", "valor_teste")
        assert get_config("chave_teste") == "valor_teste"

    def test_get_config_padrao(self):
        assert get_config("chave_inexistente", "default") == "default"

    def test_set_config_sobrescreve(self):
        set_config("chave_x", "primeiro")
        set_config("chave_x", "segundo")
        assert get_config("chave_x") == "segundo"


class TestCadastroPadrinho:

    def test_cadastrar_padrinho_aparece_na_listagem(self):
        cadastrar_padrinho("João Silva", "123456", "joao@x.com", "31900000000", "Manhã")
        lista = get_todos_padrinhos()
        nomes = [p["nome"] for p in lista]
        assert "João Silva" in nomes

    def test_cadastrar_padrinho_recupera_por_id(self):
        cadastrar_padrinho("Maria Lima", "654321", "maria@x.com", "31900000001", "Noite")
        conn = get_conn()
        row = conn.execute("SELECT id FROM padrinhos WHERE matricula='654321'").fetchone()
        conn.close()
        p = get_padrinho(row["id"])
        assert p["nome"] == "Maria Lima"
        assert p["turno"] == "Noite"
