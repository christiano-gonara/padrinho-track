import pytest
import sqlite3
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, get_conn
import database as db_module
from models import (
    calcular_status,
    emitir_advertencias_falta,
    registrar_entrega_tema,
    marcar_tema_nao_entregue,
    emitir_advertencia_manual,
    cadastrar_padrinho,
    criar_reuniao,
    lancar_presenca,
    registrar_tema,
)


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    """Cria um banco limpo e temporário para cada teste."""
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


# ── calcular_status ────────────────────────────────────────────────────────

def _criar_reunioes(n):
    for i in range(n):
        criar_reuniao(f"2026-0{i % 9 + 1}-{i // 9 * 7 + 1:02d}", f"Reunião {i + 1}", "")


class TestCalcularStatus:

    def test_sem_advertencias_retorna_apto(self):
        _criar_reunioes(2)
        pid = _padrinho()
        status = calcular_status(pid)
        assert status["status"] == "apto"
        assert status["amarelos"] == 0
        assert status["vermelhos"] == 0

    def test_um_amarelo_retorna_alerta(self):
        _criar_reunioes(2)  # limite=2: 1 amarelo → alerta
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid)
        assert status["status"] == "alerta"
        assert status["amarelos"] == 1

    def test_dois_amarelos_retorna_inapto_amarelo(self):
        _criar_reunioes(2)  # limite=2: 2 amarelos → inapto
        pid = _padrinho()
        _inserir_advertencia(pid, "amarelo")
        _inserir_advertencia(pid, "amarelo")
        status = calcular_status(pid)
        assert status["status"] == "inapto_amarelo"
        assert status["amarelos"] == 2

    def test_tres_amarelos_continua_inapto_amarelo(self):
        _criar_reunioes(3)  # limite=3: 3 amarelos → inapto
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
        _criar_reunioes(3)  # limite=3: pid1 com 2 amarelos → alerta, pid2 → apto
        pid1 = _padrinho("Padrinho A", "999001")
        pid2 = _padrinho("Padrinho B", "999002")
        _inserir_advertencia(pid1, "amarelo")
        _inserir_advertencia(pid1, "amarelo")
        status2 = calcular_status(pid2)
        assert status2["status"] == "apto"


# ── emitir_advertencias_falta ──────────────────────────────────────────────

class TestEmitirAdvertenciasFalta:

    def _setup_reuniao(self, pid):
        criar_reuniao("2026-05-01", "Teste", "")
        conn = get_conn()
        reuniao_id = conn.execute("SELECT id FROM reunioes ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        return reuniao_id

    def test_falta_sem_justificativa_gera_amarelo(self):
        pid = _padrinho()
        rid = self._setup_reuniao(pid)
        lancar_presenca(rid, pid, presente=0, justificada=0)
        emitir_advertencias_falta(rid)
        status = calcular_status(pid)
        assert status["amarelos"] == 1

    def test_presenca_nao_gera_advertencia(self):
        pid = _padrinho()
        rid = self._setup_reuniao(pid)
        lancar_presenca(rid, pid, presente=1, justificada=0)
        emitir_advertencias_falta(rid)
        status = calcular_status(pid)
        assert status["amarelos"] == 0

    def test_falta_justificada_nao_gera_advertencia(self):
        pid = _padrinho()
        rid = self._setup_reuniao(pid)
        lancar_presenca(rid, pid, presente=0, justificada=1)
        emitir_advertencias_falta(rid)
        status = calcular_status(pid)
        assert status["amarelos"] == 0

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
        status = calcular_status(pid)
        assert status["amarelos"] == 2
        assert status["status"] == "inapto_amarelo"


# ── registrar_entrega_tema ─────────────────────────────────────────────────

class TestRegistrarEntregaTema:

    def _setup_tema(self, pid, data_limite):
        registrar_tema("Tema Teste", "2026-01-01", data_limite, [pid])
        conn = get_conn()
        tema_id = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        return tema_id

    def test_entrega_no_prazo_nao_gera_advertencia(self):
        pid = _padrinho()
        tid = self._setup_tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-10")
        assert situacao == "entregue"
        assert calcular_status(pid)["amarelos"] == 0

    def test_entrega_antes_do_prazo_nao_gera_advertencia(self):
        pid = _padrinho()
        tid = self._setup_tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-08")
        assert situacao == "entregue"
        assert calcular_status(pid)["amarelos"] == 0

    def test_entrega_com_1_dia_atraso_gera_amarelo(self):
        pid = _padrinho()
        tid = self._setup_tema(pid, "2026-05-10")
        situacao = registrar_entrega_tema(tid, "2026-05-11")
        assert situacao == "atraso"
        assert calcular_status(pid)["amarelos"] == 1

    def test_entrega_com_mais_de_1_dia_gera_vermelho(self):
        pid = _padrinho()
        tid = self._setup_tema(pid, "2026-05-10")
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


# ── calcular_status com limite configurável ───────────────────────────────────

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


# ── idempotência ───────────────────────────────────────────────────────────────

class TestIdempotencia:

    def _setup_reuniao(self, pid):
        criar_reuniao("2026-05-01", "Teste", "")
        conn = get_conn()
        rid = conn.execute("SELECT id FROM reunioes ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        return rid

    def _setup_tema(self, pid, data_limite="2026-05-10"):
        registrar_tema("Tema Idempotente", "2026-01-01", data_limite, [pid])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        return tid

    def test_emitir_advertencias_falta_idempotente(self):
        """Chamar emitir_advertencias_falta duas vezes para a mesma reunião não duplica amarelos."""
        pid = _padrinho()
        rid = self._setup_reuniao(pid)
        lancar_presenca(rid, pid, presente=0, justificada=0)
        emitir_advertencias_falta(rid)
        emitir_advertencias_falta(rid)
        assert calcular_status(pid)["amarelos"] == 1

    def test_emitir_advertencias_falta_duas_reunioes_distintas(self):
        """Faltas em duas reuniões diferentes geram dois amarelos mesmo sendo chamado em sequência."""
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

    def test_registrar_entrega_tema_idempotente(self):
        """Registrar entrega do mesmo tema duas vezes não duplica advertências."""
        pid = _padrinho()
        tid = self._setup_tema(pid)
        registrar_entrega_tema(tid, "2026-05-11")  # 1 dia de atraso → amarelo
        registrar_entrega_tema(tid, "2026-05-11")  # segunda chamada deve ser ignorada
        assert calcular_status(pid)["amarelos"] == 1

    def test_marcar_tema_nao_entregue_idempotente(self):
        """Marcar tema não entregue duas vezes não duplica vermelho."""
        pid = _padrinho()
        tid = self._setup_tema(pid)
        marcar_tema_nao_entregue(tid)
        marcar_tema_nao_entregue(tid)
        assert calcular_status(pid)["vermelhos"] == 1


# ── marcar_tema_nao_entregue ──────────────────────────────────────────────────

class TestMarcarTemaNaoEntregue:

    def _setup_tema(self, pid, data_limite="2026-05-10"):
        registrar_tema("Tema Não Entregue", "2026-01-01", data_limite, [pid])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()
        return tid

    def test_nao_entregue_gera_vermelho(self):
        pid = _padrinho()
        tid = self._setup_tema(pid)
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