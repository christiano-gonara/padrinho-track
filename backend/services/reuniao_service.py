import os
import tempfile

from backend.integrations.importers import importar_presencas_csv, sincronizar_presencas_sheets
from backend.models import (
    criar_reuniao,
    editar_reuniao as atualizar_reuniao,
    excluir_reuniao as remover_reuniao,
    get_config,
    get_presencas_reuniao,
    get_todas_reunioes,
    get_todos_padrinhos,
    registrar_log,
    set_config,
)
from backend.repositories import reuniao_repository
from backend.services.status_service import emitir_advertencias_falta


def montar_contexto_reunioes():
    """Monta lista de reuniões e URL do Forms de presença."""
    return {
        "reunioes": get_todas_reunioes(),
        "sheets_presenca_url": get_config("sheets_presenca_url", ""),
    }


def criar_nova_reuniao(data, tema, descricao):
    """Cria uma reunião com data, tema e descrição."""
    criar_reuniao(data, tema.strip(), descricao.strip())


def sincronizar_presencas(reuniao_id):
    """Busca presenças no Google Sheets e monta mensagem de resultado."""
    resultado = sincronizar_presencas_sheets(reuniao_id)
    msg = f"{resultado['registradas']} presença(s) registrada(s)."
    if resultado["nao_reconhecidas"]:
        nomes = ", ".join(resultado["nao_reconhecidas"][:5])
        msg += f" {len(resultado['nao_reconhecidas'])} não reconhecida(s): {nomes}"
    registrar_log("SINCRONIZAR_PRESENCAS", msg)
    return msg


def salvar_link_forms_presenca(url):
    """Salva o link da planilha de respostas do Forms de presença."""
    set_config("sheets_presenca_url", url.strip())
    registrar_log("ALTERACAO_CONFIG", "URL da planilha de presença atualizada.")


def excluir_reuniao(reuniao_id):
    """Remove uma reunião e suas presenças associadas."""
    remover_reuniao(reuniao_id)


def editar_reuniao(reuniao_id, data, tema, descricao):
    """Atualiza os dados básicos de uma reunião."""
    atualizar_reuniao(reuniao_id, data, tema.strip(), descricao.strip())
    registrar_log("EDICAO_REUNIAO", f"Reunião ID {reuniao_id} atualizada.")


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
