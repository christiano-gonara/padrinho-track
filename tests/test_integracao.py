"""Testes de integração — rotas HTTP retornam 200 ou 302, nunca 404 ou 500."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-integration-key")
os.environ.setdefault("APP_PASSWORD", "test-password")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import database as db_module
from database import init_db, get_conn


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com banco isolado e dados mínimos de seed."""
    db_path = tmp_path / "test_integracao.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()

    conn = get_conn()
    conn.execute(
        "INSERT INTO padrinhos (nome, matricula, email, telefone, turno) VALUES (?,?,?,?,?)",
        ("Padrinho Teste", "999001", "p@test.com", "31900000001", "Noite"),
    )
    conn.execute(
        "INSERT INTO calouros (nome, telefone, turno, genero, primeiro_periodo) VALUES (?,?,?,?,?)",
        ("Calouro Teste", "31900000002", "Noite", "M", 1),
    )
    conn.execute(
        "INSERT INTO reunioes (data, tema, descricao) VALUES (?,?,?)",
        ("2026-05-01", "Reunião Teste", ""),
    )
    conn.execute("INSERT INTO matches (padrinho_id, calouro_id) VALUES (1, 1)")
    conn.execute(
        "INSERT INTO temas (titulo, data_aviso, data_limite, situacao) VALUES (?,?,?,?)",
        ("Tema Teste", "2026-05-01", "2026-05-15", "pendente"),
    )
    conn.execute("INSERT INTO tema_padrinhos (tema_id, padrinho_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


class TestGetPages:

    def test_dashboard(self, client):
        assert client.get("/").status_code == 200

    def test_padrinhos(self, client):
        assert client.get("/padrinhos").status_code == 200

    def test_padrinho_detalhe(self, client):
        assert client.get("/padrinhos/1").status_code == 200

    def test_calouros(self, client):
        assert client.get("/calouros").status_code == 200

    def test_reunioes(self, client):
        assert client.get("/reunioes").status_code == 200

    def test_presencas_get(self, client):
        assert client.get("/presencas/1").status_code == 200

    def test_temas(self, client):
        assert client.get("/temas").status_code == 200

    def test_match(self, client):
        assert client.get("/match").status_code == 200

    def test_match_lista_contatos(self, client):
        assert client.get("/match/lista-contatos").status_code == 200

    def test_inicio_semestre(self, client):
        assert client.get("/inicio").status_code == 200

    def test_advertencias(self, client):
        assert client.get("/advertencias").status_code == 200

    def test_logs(self, client):
        assert client.get("/logs").status_code == 200

    def test_configuracoes(self, client):
        assert client.get("/config").status_code == 200

    def test_relatorio(self, client):
        assert client.get("/relatorio").status_code == 200

    def test_relatorio_aptidao(self, client):
        assert client.get("/relatorio/aptidao").status_code == 200

    def test_relatorio_resumo(self, client):
        assert client.get("/relatorio/resumo").status_code == 200



class TestPostActions:

    def test_nova_reuniao(self, client):
        r = client.post("/reunioes/nova", data={
            "data": "2026-06-01",
            "tema": "Reunião Nova",
            "descricao": "",
        })
        assert r.status_code == 302

    def test_novo_tema(self, client):
        r = client.post("/temas/novo", data={
            "titulo": "Tema Novo",
            "data_aviso": "2026-06-01",
            "data_limite": "2026-06-08",
            "padrinho_ids": ["1"],
        })
        assert r.status_code == 302

    def test_match_rodar(self, client):
        assert client.post("/match/rodar").status_code == 302

    def test_sincronizar_presenca_sem_config(self, client):
        assert client.post("/reunioes/1/sincronizar").status_code == 302

    def test_importar_padrinhos_sem_url(self, client):
        assert client.post("/inicio/importar-padrinhos", data={}).status_code == 302

    def test_importar_calouros_sem_url(self, client):
        assert client.post("/inicio/importar-calouros", data={}).status_code == 302

    def test_lancar_presencas(self, client):
        r = client.post("/presencas/1", data={"presentes": ["1"]})
        assert r.status_code == 302
