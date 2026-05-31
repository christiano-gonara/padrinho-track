"""Testes do algoritmo de match padrinho-calouro."""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import rodar_match, cadastrar_padrinho


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    yield


class TestRodarMatch:

    def test_banco_vazio_retorna_sem_matches(self):
        resultado = rodar_match()
        assert resultado["resultado"] == []
        assert resultado["sem_match"] == []

    def test_padrinho_sem_calouros_retorna_lista_vazia(self):
        cadastrar_padrinho("Padrinho X", "111001", "x@x.com", "31900000000", "Noite")
        resultado = rodar_match()
        assert len(resultado["resultado"]) == 1
        assert resultado["resultado"][0]["total"] == 0

    def test_match_com_padrinho_e_calouro_cria_atribuicao(self):
        cadastrar_padrinho("Padrinho Y", "222001", "y@y.com", "31900000000", "Noite")
        conn = get_conn()
        conn.execute(
            "INSERT INTO calouros (nome, telefone, turno, genero) VALUES (?,?,?,?)",
            ("Calouro Y", "31900000001", "Noite", "M"),
        )
        conn.commit()
        conn.close()
        resultado = rodar_match()
        assert resultado["resultado"][0]["total"] == 1

    def test_turno_igual_aumenta_score(self):
        cadastrar_padrinho("Padrinho Manhã", "333001", "m@m.com", "31900000000", "Manhã")
        cadastrar_padrinho("Padrinho Noite", "333002", "n@n.com", "31900000000", "Noite")
        conn = get_conn()
        conn.execute(
            "INSERT INTO calouros (nome, telefone, turno, genero) VALUES (?,?,?,?)",
            ("Calouro Manhã", "31900000001", "Manhã", "M"),
        )
        conn.commit()
        conn.close()
        resultado = rodar_match()
        atribuicoes = {r["padrinho"]["turno"]: r["total"] for r in resultado["resultado"]}
        assert atribuicoes.get("Manhã", 0) == 1
        assert atribuicoes.get("Noite", 0) == 0
