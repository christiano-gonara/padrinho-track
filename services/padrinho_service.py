import sqlite3

from models import (
    cadastrar_padrinho,
    contar_reunioes,
    editar_padrinho as atualizar_padrinho,
    excluir_padrinho as remover_padrinho,
    get_historico_padrinho,
    get_padrinho,
    get_todos_padrinhos,
    registrar_log,
    redistribuir_calouros,
)
from services.status_service import calcular_status, calcular_todos_status, get_advertencias_padrinho
from repositories import padrinho_repository


def listar_padrinhos_com_status():
    """Retorna os padrinhos ativos já com o status de aptidão calculado."""
    lista = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in lista], limite)
    padrinhos_com_status = []
    for p in lista:
        d = dict(p)
        d["status"] = todos_status.get(p["id"], {"status": "apto"})["status"]
        padrinhos_com_status.append(d)
    return padrinhos_com_status


def cadastrar_novo_padrinho(nome, matricula, email, telefone, turno):
    """Cadastra um padrinho e devolve mensagem pronta para flash."""
    nome = nome.strip()
    matricula = matricula.strip()
    try:
        cadastrar_padrinho(nome, matricula, email.strip(), telefone.strip(), turno.strip())
    except sqlite3.IntegrityError:
        return False, "Matrícula já cadastrada."

    registrar_log("CADASTRO_PADRINHO", f"Padrinho '{nome}' (matrícula {matricula}) cadastrado.")
    return True, "Padrinho cadastrado com sucesso."


def montar_contexto_padrinho_detalhe(padrinho_id):
    """Agrupa todos os dados necessários para renderizar o detalhe do padrinho."""
    return {
        "padrinho": get_padrinho(padrinho_id),
        "status": calcular_status(padrinho_id),
        "historico": get_historico_padrinho(padrinho_id),
        "advertencias": get_advertencias_padrinho(padrinho_id),
        "calouros_match": padrinho_repository.listar_calouros_do_padrinho(padrinho_id),
        "todos_padrinhos": padrinho_repository.listar_ativos_id_nome_exceto(padrinho_id),
    }


def redistribuir_padrinho(padrinho_id, form_items):
    """Redistribui calouros antes de remover/desativar um padrinho."""
    redistribuicao = {}
    for key, value in form_items:
        if key.startswith("calouro_"):
            calouro_id = int(key.split("_")[1])
            redistribuicao[calouro_id] = int(value) if value else None
    redistribuir_calouros(padrinho_id, redistribuicao)
    registrar_log("REMOCAO_PADRINHO", f"Padrinho ID {padrinho_id} removido do programa. Calouros redistribuídos.")


def editar_padrinho(padrinho_id, form):
    """Atualiza dados cadastrais e demográficos de um padrinho."""
    nome = form["nome"].strip()
    idade_s = form.get("idade", "").strip()
    passou_s = form.get("passou_algoritmos", "")
    atualizar_padrinho(
        padrinho_id,
        nome,
        form["matricula"].strip(),
        form.get("email", "").strip(),
        form.get("telefone", "").strip(),
        form.get("turno", "").strip(),
        genero=form.get("genero", "").strip() or None,
        idade=int(idade_s) if idade_s.isdigit() else None,
        cidade_bh=1 if form.get("cidade_bh") else 0,
        bolsista=1 if form.get("bolsista") else 0,
        trabalha=1 if form.get("trabalha") else 0,
        periodo=form.get("periodo", "").strip() or None,
        passou_algoritmos=int(passou_s) if passou_s in ("0", "1") else None,
    )
    registrar_log("EDICAO_PADRINHO", f"Padrinho '{nome}' (ID {padrinho_id}) atualizado.")


def excluir_padrinho(padrinho_id):
    """Desativa um padrinho e registra a ação no log."""
    padrinho = get_padrinho(padrinho_id)
    remover_padrinho(padrinho_id)
    if padrinho:
        registrar_log("EXCLUSAO_PADRINHO", f"Padrinho '{padrinho['nome']}' (ID {padrinho_id}) removido do programa.")
