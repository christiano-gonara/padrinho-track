import json
import os
from datetime import datetime, date

from repositories import (
    advertencia_repository,
    config_repository,
    log_repository,
    match_repository,
    padrinho_repository,
    presenca_repository,
    reuniao_repository,
    tema_repository,
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_semestre.json")

_CONFIG_DEFAULTS = {
    "semestre": "2026/1",
    "professor_coordenador": "Prof. Laerte Xavier",
    "programa": "Mentoria Acadêmica — Engenharia de Software",
    "instituicao": "PUC Minas",
    "total_reunioes": 3,
    "data_inicio": "2026-03-01",
    "data_fim": "2026-07-15",
    "coordenadora_geral": "",
    "coordenadores": [],
}

_PREPS = {"de", "da", "do", "dos", "das", "e", "di", "von", "van", "el"}


def get_config_semestre():
    """Carrega configurações do semestre com fallback para valores padrão."""
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            loaded = json.load(f)
        return {**_CONFIG_DEFAULTS, **loaded}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_CONFIG_DEFAULTS)


def salvar_config_semestre(dados):
    """Salva configurações do semestre em JSON."""
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def abreviar_nome(nome):
    """Abrevia nomes longos mantendo primeiro e último sobrenome."""
    if not nome:
        return nome
    partes = nome.split()
    if len(partes) <= 2:
        return nome
    primeiro = partes[0]
    ultimo_idx = len(partes) - 1
    while ultimo_idx > 0 and partes[ultimo_idx].lower() in _PREPS:
        ultimo_idx -= 1
    ultimo = partes[ultimo_idx]
    meios = [p[0].upper() + "." for p in partes[1:ultimo_idx] if p.lower() not in _PREPS]
    if meios:
        return primeiro + " " + " ".join(meios) + " " + ultimo
    return primeiro + " " + ultimo


def registrar_log(acao, descricao):
    """Compatibilidade: registra log operacional."""
    try:
        from flask import request
        ip = request.remote_addr
    except RuntimeError:
        ip = None
    log_repository.registrar(acao, descricao, ip)


def get_todos_padrinhos():
    return padrinho_repository.listar_ativos()


def get_padrinho(padrinho_id):
    return padrinho_repository.buscar_por_id(padrinho_id)


def cadastrar_padrinho(nome, matricula, email, telefone, turno):
    return padrinho_repository.cadastrar(nome, matricula, email, telefone, turno)


def editar_padrinho(padrinho_id, nome, matricula, email, telefone, turno,
                    genero=None, idade=None, cidade_bh=None, bolsista=None,
                    trabalha=None, periodo=None, passou_algoritmos=None):
    return padrinho_repository.atualizar(
        padrinho_id, nome, matricula, email, telefone, turno,
        genero, idade, cidade_bh, bolsista, trabalha, periodo, passou_algoritmos,
    )


def excluir_padrinho(padrinho_id):
    return padrinho_repository.desativar(padrinho_id)


def redistribuir_calouros(padrinho_id, redistribuicao):
    return padrinho_repository.redistribuir_calouros_e_desativar(padrinho_id, redistribuicao)


def get_todas_reunioes():
    return reuniao_repository.listar_todas_desc()


def contar_reunioes():
    return reuniao_repository.contar_todas()


def criar_reuniao(data, tema, descricao):
    return reuniao_repository.criar(data, tema, descricao)


def editar_reuniao(reuniao_id, data, tema, descricao):
    return reuniao_repository.atualizar(reuniao_id, data, tema, descricao)


def excluir_reuniao(reuniao_id):
    return reuniao_repository.excluir(reuniao_id)


def lancar_presenca(reuniao_id, padrinho_id, presente, justificada):
    return reuniao_repository.salvar_presenca(reuniao_id, padrinho_id, presente, justificada)


def get_presencas_reuniao(reuniao_id):
    return presenca_repository.listar_por_reuniao(reuniao_id)


def get_todos_temas():
    return tema_repository.listar_com_responsaveis()


def registrar_tema(titulo, data_aviso, data_limite, padrinho_ids):
    return tema_repository.criar(titulo, data_aviso, data_limite, padrinho_ids)


def _emitir_advertencias_tema(tema_id, tipo, origem, motivo):
    hoje = date.today().isoformat()
    registros = [
        (padrinho_id, tipo, origem, motivo, hoje)
        for padrinho_id in tema_repository.listar_padrinho_ids(tema_id)
    ]
    advertencia_repository.criar_varias(registros)


def registrar_entrega_tema(tema_id, data_entrega_str):
    """Registra entrega de tema e emite advertência conforme atraso."""
    tema = tema_repository.buscar_por_id(tema_id)
    if tema["situacao"] not in (None, "pendente"):
        return tema["situacao"]

    data_limite = datetime.strptime(tema["data_limite"], "%Y-%m-%d").date()
    data_entrega = datetime.strptime(data_entrega_str, "%Y-%m-%d").date()
    diff = (data_entrega - data_limite).days

    if diff <= 0:
        situacao = "entregue"
    elif diff == 1:
        situacao = "atraso"
    else:
        situacao = "nao_entregue"

    tema_repository.atualizar_entrega(tema_id, data_entrega_str, situacao)

    if situacao == "atraso":
        _emitir_advertencias_tema(tema_id, "amarelo", "atraso_tema", f"Entrega com atraso: {tema['titulo']}")
    elif situacao == "nao_entregue":
        _emitir_advertencias_tema(tema_id, "vermelho", "nao_entrega", f"Não entregou: {tema['titulo']}")
    return situacao


def marcar_tema_nao_entregue(tema_id):
    """Marca tema como não entregue e emite vermelho aos responsáveis."""
    tema = tema_repository.buscar_por_id(tema_id)
    if tema["situacao"] not in (None, "pendente"):
        return
    tema_repository.marcar_situacao(tema_id, "nao_entregue")
    _emitir_advertencias_tema(tema_id, "vermelho", "nao_entrega", f"Não entregou: {tema['titulo']}")


def editar_tema(tema_id, titulo, data_aviso, data_limite, padrinho_ids):
    return tema_repository.atualizar(tema_id, titulo, data_aviso, data_limite, padrinho_ids)


def excluir_tema(tema_id):
    return tema_repository.excluir(tema_id)


def emitir_advertencias_falta(reuniao_id):
    from services.status_service import emitir_advertencias_falta as _emitir
    return _emitir(reuniao_id)


def emitir_advertencia_manual(padrinho_id, motivo, tipo="vermelho"):
    from services.status_service import emitir_advertencia_manual as _emitir
    return _emitir(padrinho_id, motivo, tipo)


def get_advertencias_padrinho(padrinho_id):
    from services.status_service import get_advertencias_padrinho as _listar
    return _listar(padrinho_id)


def calcular_status(padrinho_id, limite=None):
    from services.status_service import calcular_status as _calcular
    return _calcular(padrinho_id, limite)


def calcular_todos_status(padrinho_ids, limite=None):
    from services.status_service import calcular_todos_status as _calcular
    return _calcular(padrinho_ids, limite)


def get_config(chave, padrao=None):
    return config_repository.obter(chave, padrao)


def set_config(chave, valor):
    return config_repository.salvar(chave, valor)


def get_historico_padrinho(padrinho_id):
    return {
        "presencas": presenca_repository.listar_historico_padrinho(padrinho_id),
        "temas": tema_repository.listar_historico_padrinho(padrinho_id),
    }


def get_relatorio_geral():
    padrinhos = get_todos_padrinhos()
    if not padrinhos:
        return []
    padrinho_ids = [p["id"] for p in padrinhos]
    limite = contar_reunioes()
    todos_status = calcular_todos_status(padrinho_ids, limite)
    pres_rows = presenca_repository.contar_por_padrinhos(padrinho_ids)
    pres_map = {r["padrinho_id"]: (r["total"], r["presentes"] or 0) for r in pres_rows}

    relatorio = []
    for p in padrinhos:
        st = todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})
        total_r, presentes = pres_map.get(p["id"], (0, 0))
        relatorio.append({
            "padrinho": p,
            "status": st["status"],
            "amarelos": st["amarelos"],
            "vermelhos": st["vermelhos"],
            "total_reunioes": total_r,
            "total_presentes": presentes,
        })
    return relatorio


def get_calouros_match_completo():
    return match_repository.listar_calouros_por_padrinho_completo()


def excluir_advertencia(advertencia_id):
    return advertencia_repository.excluir(advertencia_id)


def rodar_match(max_calouros=3, score_minimo=0):
    from services.match_algorithm import rodar_match as _rodar_match
    return _rodar_match(max_calouros, score_minimo)
