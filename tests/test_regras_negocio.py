"""Testes das regras de negócio essenciais: cálculo de status, faltas e temas."""

from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_conn, init_db
import backend.database as db_module
from backend.models import (
    cadastrar_padrinho,
    calcular_status,
    criar_reuniao,
    emitir_advertencia_manual,
    emitir_advertencias_falta,
    lancar_presenca,
    marcar_tema_nao_entregue,
    registrar_entrega_tema,
    registrar_tema,
)


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    yield


def _criar_padrinho(nome="Padrinho Teste", matricula="999001"):
    cadastrar_padrinho(nome, matricula, f"{matricula}@exemplo.com", "31900000000", "Noite")
    conn = get_conn()
    row = conn.execute("SELECT id FROM padrinhos WHERE matricula=?", (matricula,)).fetchone()
    conn.close()
    return row["id"]


def _criar_reuniao(titulo="Reunião Teste"):
    criar_reuniao("2026-05-01", titulo, "")
    conn = get_conn()
    row = conn.execute("SELECT id FROM reunioes ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row["id"]


class TestStatusEAdvertencias:
    """Valida as regras de aptidão ao ACG e emissão de advertências."""

    def test_progressao_status_por_faltas_amarelas(self):
        """0 faltas = apto; 1 falta = alerta; 2 faltas = inapto por amarelos."""
        pid = _criar_padrinho()
        r1 = _criar_reuniao("R1")
        r2 = _criar_reuniao("R2")

        # Inicialmente apto
        status_inicial = calcular_status(pid)
        assert status_inicial["status"] == "apto"
        assert status_inicial["amarelos"] == 0

        # Primeira falta não justificada -> alerta (1 amarelo)
        lancar_presenca(r1, pid, presente=0, justificada=0)
        emitir_advertencias_falta(r1)
        status_alerta = calcular_status(pid)
        assert status_alerta["status"] == "alerta"
        assert status_alerta["amarelos"] == 1

        # Segunda falta não justificada -> inapto por amarelos (atinge limite)
        lancar_presenca(r2, pid, presente=0, justificada=0)
        emitir_advertencias_falta(r2)
        status_inapto = calcular_status(pid)
        assert status_inapto["status"] == "inapto_amarelo"
        assert status_inapto["amarelos"] == 2

    def test_advertencia_vermelha_invalida_imediatamente(self):
        """Uma advertência vermelha (manual ou grave) torna inapto imediatamente."""
        pid = _criar_padrinho()
        emitir_advertencia_manual(pid, "Conduta incompatível com as diretrizes do programa")

        status = calcular_status(pid)
        assert status["status"] == "inapto_vermelho"
        assert status["vermelhos"] == 1

    def test_status_independente_entre_padrinhos(self):
        """Penalidades de um padrinho não interferem no status dos demais."""
        p1 = _criar_padrinho("Padrinho Um", "111001")
        p2 = _criar_padrinho("Padrinho Dois", "222002")

        emitir_advertencia_manual(p1, "Infração grave")
        assert calcular_status(p1)["status"] == "inapto_vermelho"
        assert calcular_status(p2)["status"] == "apto"


class TestPresencas:
    """Valida presenças, faltas justificadas e idempotência."""

    def test_presenca_e_falta_justificada_nao_geram_advertencia(self):
        pid = _criar_padrinho()
        r1 = _criar_reuniao("R1")
        r2 = _criar_reuniao("R2")

        # R1 presente
        lancar_presenca(r1, pid, presente=1, justificada=0)
        emitir_advertencias_falta(r1)

        # R2 falta justificada
        lancar_presenca(r2, pid, presente=0, justificada=1)
        emitir_advertencias_falta(r2)

        status = calcular_status(pid)
        assert status["amarelos"] == 0
        assert status["status"] == "apto"

    def test_emissao_advertencia_falta_idempotente(self):
        """Reprocessar advertências da mesma reunião não duplica advertências."""
        pid = _criar_padrinho()
        r1 = _criar_reuniao("R1")

        lancar_presenca(r1, pid, presente=0, justificada=0)
        emitir_advertencias_falta(r1)
        emitir_advertencias_falta(r1)  # chamada repetida

        status = calcular_status(pid)
        assert status["amarelos"] == 1


class TestTemas:
    """Valida entregas de temas, atrasos, não-entregas e responsabilidade em grupo."""

    def test_entrega_no_prazo_vs_com_atraso(self):
        pid = _criar_padrinho()
        registrar_tema("Tema 1", "2026-05-01", "2026-05-10", [pid])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()

        # Entrega no prazo
        situacao = registrar_entrega_tema(tid, "2026-05-10")
        assert situacao == "entregue"
        assert calcular_status(pid)["amarelos"] == 0

        # Novo tema entregue com atraso
        registrar_tema("Tema 2", "2026-05-01", "2026-05-10", [pid])
        conn = get_conn()
        tid2 = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()

        situacao2 = registrar_entrega_tema(tid2, "2026-05-11")
        assert situacao2 == "atraso"
        assert calcular_status(pid)["amarelos"] == 1

    def test_tema_nao_entregue_gera_vermelho_e_afeta_grupo(self):
        p1 = _criar_padrinho("Padrinho A", "999001")
        p2 = _criar_padrinho("Padrinho B", "999002")
        registrar_tema("Tema Compartilhado", "2026-05-01", "2026-05-10", [p1, p2])
        conn = get_conn()
        tid = conn.execute("SELECT id FROM temas ORDER BY id DESC LIMIT 1").fetchone()["id"]
        conn.close()

        marcar_tema_nao_entregue(tid)
        # Idempotência: marcar duas vezes não duplica
        marcar_tema_nao_entregue(tid)

        assert calcular_status(p1)["status"] == "inapto_vermelho"
        assert calcular_status(p2)["status"] == "inapto_vermelho"
