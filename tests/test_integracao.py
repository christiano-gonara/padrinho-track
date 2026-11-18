"""Testes de integração — landing page pública, proteção de login e fluxos principais."""

import os
from pathlib import Path
import sys

import pytest

os.environ.setdefault("SECRET_KEY", "test-integration-key")
os.environ.setdefault("APP_PASSWORD", "test-password")

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_conn, init_db
import backend.database as db_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com banco isolado e dados mínimos."""
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


class TestLandingEPublico:
    """A apresentação pública abre sem login; visitantes autenticados vão ao dashboard."""

    def test_landing_abre_sem_login(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Padrinho Track" in resp.data
        assert b'data-theme="light"' in resp.data
        assert b"prefers-color-scheme: dark" not in resp.data

    def test_visitante_autenticado_redireciona_ao_dashboard(self, client):
        with client.session_transaction() as sess:
            sess["logged_in"] = True
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]


class TestProtecaoDeAcesso:
    """Rotas internas exigem login e redirecionam para a tela de autenticação."""

    @pytest.mark.parametrize(
        "rota",
        [
            "/dashboard",
            "/padrinhos",
            "/calouros",
            "/reunioes",
            "/temas",
            "/match",
            "/relatorio",
            "/config",
        ],
    )
    def test_rotas_fechadas_redirecionam_sem_login(self, client, rota):
        resp = client.get(rota)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


class TestNavegacaoEAcoesAutenticadas:
    """Usuário autenticado consegue visualizar as páginas e executar ações chave."""

    @pytest.fixture(autouse=True)
    def autenticar(self, client):
        with client.session_transaction() as sess:
            sess["logged_in"] = True

    @pytest.mark.parametrize(
        "rota",
        [
            "/dashboard",
            "/padrinhos",
            "/padrinhos/1",
            "/calouros",
            "/reunioes",
            "/presencas/1",
            "/temas",
            "/inicio",
            "/advertencias",
            "/match",
            "/match/lista-contatos",
            "/relatorio",
            "/relatorio/aptidao",
            "/relatorio/resumo",
            "/relatorio/certificado/1",
            "/config",
            "/logs",
        ],
    )
    def test_rotas_principais_respondem_200(self, client, rota):
        resp = client.get(rota)
        assert resp.status_code == 200

    def test_acoes_post_essenciais(self, client):
        # Lançar presença
        r_presenca = client.post("/presencas/1", data={"presentes": ["1"]})
        assert r_presenca.status_code == 302

        # Nova reunião
        r_reuniao = client.post(
            "/reunioes/nova",
            data={"data": "2026-06-01", "tema": "Nova Reunião", "descricao": ""},
        )
        assert r_reuniao.status_code == 302

        # Rodar match
        r_match = client.post("/match/rodar")
        assert r_match.status_code == 302

    def test_api_rest_para_frontend_react(self, client):
        # /api/auth/me responde autenticado
        r_me = client.get("/api/auth/me")
        assert r_me.status_code == 200
        assert r_me.get_json()["authenticated"] is True

        # Endpoints JSON principais para React + TypeScript
        for rota in ["/api/dashboard", "/api/padrinhos", "/api/reunioes", "/api/temas", "/api/match", "/api/relatorio", "/api/config"]:
            r = client.get(rota)
            assert r.status_code == 200, rota
            assert isinstance(r.get_json(), dict)
