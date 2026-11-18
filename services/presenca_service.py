import os
import tempfile

from models import (
    get_presencas_reuniao,
    get_todos_padrinhos,
    registrar_log,
)
from integrations.importers import importar_presencas_csv
from repositories import reuniao_repository
from services.status_service import emitir_advertencias_falta


def listar_presencas_reuniao(reuniao_id):
    """Lista todos os padrinhos com presença/justificativa em uma reunião."""
    return get_presencas_reuniao(reuniao_id)


def lancar_presencas_reuniao(reuniao_id, presentes_ids, justificadas_ids):
    """Salva presença manual e emite advertências automáticas de falta."""
    padrinhos = get_todos_padrinhos()
    presentes_ids = set(presentes_ids)
    justificadas_ids = set(justificadas_ids)

    registros = []
    for p in padrinhos:
        pid = str(p["id"])
        presente = 1 if pid in presentes_ids else 0
        justificada = 1 if pid in justificadas_ids else 0
        registros.append((reuniao_id, p["id"], presente, justificada))
    reuniao_repository.salvar_presencas_em_lote(registros)

    emitir_advertencias_falta(reuniao_id)
    registrar_log("LANCAMENTO_PRESENCA", f"Presenças lançadas para a reunião ID {reuniao_id}.")


def buscar_reuniao(reuniao_id):
    """Busca uma reunião para a tela de importação de CSV."""
    return reuniao_repository.buscar_por_id(reuniao_id)


def importar_presencas_upload(arquivo, reuniao_id):
    """Recebe um CSV enviado pela tela e importa presenças para uma reunião."""
    if not arquivo or not arquivo.filename.endswith(".csv"):
        return {"erro": "Envie um arquivo CSV válido."}

    tmp_path = os.path.join(tempfile.gettempdir(), f"presenca_{reuniao_id}.csv")
    arquivo.save(tmp_path)
    try:
        return importar_presencas_csv(tmp_path, reuniao_id)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def formatar_mensagem_importacao(resultado):
    """Transforma o resultado da importação em texto/categoria para flash."""
    if "erro" in resultado:
        return resultado["erro"], "error"

    msg = f"{resultado['processados']} presenças importadas."
    if resultado["nao_encontrados"]:
        msg += f" Matrículas não encontradas: {', '.join(resultado['nao_encontrados'])}"
    return msg, "success"
