from datetime import date

from models import (
    editar_tema as atualizar_tema,
    excluir_tema as remover_tema,
    get_config,
    get_todos_padrinhos,
    get_todos_temas,
    marcar_tema_nao_entregue,
    registrar_entrega_tema,
    registrar_log,
    registrar_tema,
    set_config,
)
from integrations.importers import sincronizar_responsaveis_temas


def montar_contexto_temas():
    """Monta temas, responsáveis e sugestões de vagas para a tela de temas."""
    lista = get_todos_temas()
    padrinhos = get_todos_padrinhos()
    sheets_url = get_config("sheets_inscricoes_url", "")
    total_p = len(padrinhos)
    total_t = len(lista)

    if total_t > 0 and total_p > 0:
        base = total_p // total_t
        excedente = total_p % total_t
        sugestao_vagas = {
            "base": base,
            "excedente": excedente,
            "total_padrinhos": total_p,
            "total_temas": total_t,
        }
    else:
        sugestao_vagas = None

    return {
        "temas": lista,
        "padrinhos": padrinhos,
        "today": date.today().isoformat(),
        "sheets_inscricoes_url": sheets_url,
        "sugestao_vagas": sugestao_vagas,
        "ultimo_prazo": lista[-1]["tema"]["data_limite"] if lista else "",
    }


def salvar_link_inscricoes(url):
    """Salva o link da planilha de inscrições/responsáveis por tema."""
    set_config("sheets_inscricoes_url", url.strip())
    registrar_log("ALTERACAO_CONFIG", "URL da planilha de inscrições em temas atualizada.")


def sincronizar_responsaveis():
    """Sincroniza responsáveis por tema a partir do Google Sheets."""
    resultado = sincronizar_responsaveis_temas()
    msg = f"{resultado['atualizados']} responsável(eis) atualizado(s)."
    if resultado["nao_reconhecidos"]:
        nomes = ", ".join(resultado["nao_reconhecidos"][:5])
        msg += f" {len(resultado['nao_reconhecidos'])} não reconhecido(s): {nomes}"
    registrar_log("SINCRONIZAR_TEMAS", msg)
    return msg


def criar_tema(titulo, data_aviso, data_limite, padrinho_ids):
    """Cria um tema e vincula os padrinhos responsáveis."""
    registrar_tema(titulo.strip(), data_aviso, data_limite, padrinho_ids)


def registrar_entrega(tema_id, data_entrega):
    """Registra entrega de tema e devolve a mensagem conforme prazo/status."""
    situacao = registrar_entrega_tema(tema_id, data_entrega)
    mensagens = {
        "entregue": ("Tema entregue no prazo.", "success"),
        "atraso": ("Tema entregue com atraso — amarelo emitido.", "error"),
        "nao_entregue": ("Tema não entregue — vermelho emitido.", "error"),
    }
    return mensagens.get(situacao, ("Status atualizado.", "success"))


def registrar_nao_entrega(tema_id):
    """Marca um tema como não entregue, acionando a regra de advertência."""
    marcar_tema_nao_entregue(tema_id)


def excluir_tema(tema_id):
    """Remove um tema e seus vínculos com padrinhos."""
    remover_tema(tema_id)


def editar_tema(tema_id, titulo, data_aviso, data_limite, padrinho_ids):
    """Atualiza dados de um tema e seus responsáveis."""
    atualizar_tema(tema_id, titulo.strip(), data_aviso, data_limite, padrinho_ids)
    registrar_log("EDICAO_TEMA", f"Tema ID {tema_id} atualizado.")
