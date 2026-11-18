from models import (
    criar_reuniao,
    editar_reuniao as atualizar_reuniao,
    excluir_reuniao as remover_reuniao,
    get_config,
    get_todas_reunioes,
    registrar_log,
    set_config,
)
from integrations.importers import sincronizar_presencas_sheets


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
