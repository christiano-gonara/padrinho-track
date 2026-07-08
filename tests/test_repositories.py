"""Testes básicos dos repositories de configuração e padrinhos."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db_module
from database import init_db
from repositories import config_repository, padrinho_repository


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    yield


class TestConfigRepository:

    def test_salvar_e_obter_config(self):
        config_repository.salvar("chave_teste", "valor_teste")
        assert config_repository.obter("chave_teste") == "valor_teste"

    def test_obter_config_padrao(self):
        assert config_repository.obter("chave_inexistente", "default") == "default"

    def test_salvar_config_sobrescreve(self):
        config_repository.salvar("chave_x", "primeiro")
        config_repository.salvar("chave_x", "segundo")
        assert config_repository.obter("chave_x") == "segundo"


class TestPadrinhoRepository:

    def test_cadastrar_padrinho_aparece_na_listagem(self):
        padrinho_repository.cadastrar("João Silva", "123456", "joao@x.com", "31900000000", "Manhã")
        nomes = [p["nome"] for p in padrinho_repository.listar_ativos()]
        assert "João Silva" in nomes

    def test_cadastrar_padrinho_recupera_por_id(self):
        padrinho_repository.cadastrar("Maria Lima", "654321", "maria@x.com", "31900000001", "Noite")
        padrinho = padrinho_repository.listar_ativos()[0]
        encontrado = padrinho_repository.buscar_por_id(padrinho["id"])
        assert encontrado["nome"] == "Maria Lima"
        assert encontrado["turno"] == "Noite"
