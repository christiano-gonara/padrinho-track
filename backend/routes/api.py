"""API REST em JSON para consumo do frontend React + TypeScript."""

import os
from datetime import date

from flask import Blueprint, jsonify, request, session

from backend.database import get_conn
from backend.models import (
    contar_reunioes,
    excluir_advertencia as excluir_adv_registro,
    get_calouros_match_completo,
    get_config,
    get_config_semestre,
    get_relatorio_geral,
    get_todos_padrinhos,
    registrar_log,
    salvar_config_semestre,
)
from backend.repositories import (
    advertencia_repository,
    match_repository,
    padrinho_repository,
    reuniao_repository,
    tema_repository,
)
from backend.services.match_service import gerar_e_confirmar_match, montar_contexto_match, resetar_match
from backend.services.padrinho_service import (
    cadastrar_novo_padrinho,
    editar_padrinho,
    excluir_padrinho,
    listar_padrinhos_com_status,
    montar_contexto_padrinho_detalhe,
)
from backend.services.relatorio_service import montar_contexto_relatorio_geral
from backend.services.reuniao_service import (
    buscar_reuniao,
    criar_nova_reuniao,
    editar_reuniao,
    excluir_reuniao,
    lancar_presencas_reuniao,
    listar_presencas_reuniao,
    montar_contexto_reunioes,
    salvar_link_forms_presenca,
    sincronizar_presencas,
)
from backend.services.status_service import calcular_todos_status, emitir_advertencia_manual
from backend.services.tema_service import (
    criar_tema,
    editar_tema,
    excluir_tema,
    montar_contexto_temas,
    registrar_entrega,
    registrar_nao_entrega,
    salvar_link_inscricoes,
    sincronizar_responsaveis,
)

bp = Blueprint("api", __name__, url_prefix="/api")


def _row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    return {k: row[k] for k in row.keys()}


def _rows_to_list(rows):
    return [_row_to_dict(r) for r in rows]


@bp.route("/auth/me", methods=["GET"])
def auth_me():
    return jsonify({"authenticated": bool(session.get("logged_in"))})


@bp.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    expected_user = os.environ.get("APP_USERNAME", "admin")
    expected_pass = os.environ.get("APP_PASSWORD", "")
    if username == expected_user and password == expected_pass:
        session["logged_in"] = True
        return jsonify({"ok": True, "authenticated": True})
    return jsonify({"ok": False, "error": "Usuário ou senha inválidos."}), 401


@bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"ok": True, "authenticated": False})


@bp.route("/dashboard", methods=["GET"])
def api_dashboard():
    padrinhos = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    dados = []
    for p in padrinhos:
        s = todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})
        dados.append({
            "padrinho": _row_to_dict(p),
            "status": s["status"],
            "amarelos": s["amarelos"],
            "vermelhos": s["vermelhos"],
        })

    reunioes_lista = reuniao_repository.listar_todas_asc()
    contagem = {r["reuniao_id"]: r for r in reuniao_repository.contar_presencas_por_reuniao()}
    presencas_por_reuniao = []
    for r in reunioes_lista:
        c = contagem.get(r["id"])
        presentes = (c["presentes"] or 0) if c else 0
        total_reg = (c["total"] or 0) if c else 0
        partes = r["data"].split("-") if r["data"] else []
        label = f"{partes[2]}/{partes[1]}" if len(partes) == 3 else (r["data"] or "—")
        presencas_por_reuniao.append({
            "id": r["id"],
            "label": label,
            "tema": r["tema"] or "Reunião",
            "presentes": presentes,
            "ausentes": max(0, total_reg - presentes),
        })

    return jsonify({
        "dados": dados,
        "presencas_por_reuniao": presencas_por_reuniao,
        "proxima_reuniao": _row_to_dict(reuniao_repository.buscar_ultima()),
        "proximo_tema": _row_to_dict(tema_repository.buscar_proximo_pendente()),
        "config": get_config_semestre(),
    })


@bp.route("/padrinhos", methods=["GET", "POST"])
def api_padrinhos():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        ok, msg = cadastrar_novo_padrinho(
            data.get("nome", ""),
            data.get("matricula", ""),
            data.get("email", ""),
            data.get("telefone", ""),
            data.get("turno", ""),
        )
        return jsonify({"ok": ok, "message": msg}), (201 if ok else 400)
    return jsonify({"padrinhos": listar_padrinhos_com_status()})


@bp.route("/padrinhos/<int:padrinho_id>", methods=["GET", "PUT", "DELETE"])
def api_padrinho_detalhe(padrinho_id):
    if request.method == "DELETE":
        excluir_padrinho(padrinho_id)
        return jsonify({"ok": True})
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        editar_padrinho(padrinho_id, data)
        return jsonify({"ok": True})

    ctx = montar_contexto_padrinho_detalhe(padrinho_id)
    if not ctx["padrinho"]:
        return jsonify({"error": "Padrinho não encontrado."}), 404
    return jsonify({
        "padrinho": _row_to_dict(ctx["padrinho"]),
        "status": ctx["status"],
        "historico": {
            "presencas": _rows_to_list(ctx["historico"]["presencas"]),
            "temas": _rows_to_list(ctx["historico"]["temas"]),
        },
        "advertencias": _rows_to_list(ctx["advertencias"]),
        "calouros_match": _rows_to_list(ctx["calouros_match"]),
        "todos_padrinhos": _rows_to_list(ctx["todos_padrinhos"]),
    })


@bp.route("/calouros", methods=["GET"])
def api_calouros():
    grupos = get_calouros_match_completo()
    return jsonify({
        "grupos": [
            {"padrinho": _row_to_dict(g["padrinho"]), "calouros": _rows_to_list(g["calouros"])}
            for g in grupos
        ]
    })


@bp.route("/reunioes", methods=["GET", "POST"])
def api_reunioes():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        criar_nova_reuniao(data.get("data", ""), data.get("tema", ""), data.get("descricao", ""))
        return jsonify({"ok": True}), 201
    ctx = montar_contexto_reunioes()
    return jsonify({
        "reunioes": _rows_to_list(ctx["reunioes"]),
        "sheets_presenca_url": ctx["sheets_presenca_url"],
    })


@bp.route("/reunioes/<int:reuniao_id>", methods=["PUT", "DELETE"])
def api_reuniao_item(reuniao_id):
    if request.method == "DELETE":
        excluir_reuniao(reuniao_id)
        return jsonify({"ok": True})
    data = request.get_json(silent=True) or {}
    editar_reuniao(reuniao_id, data.get("data", ""), data.get("tema", ""), data.get("descricao", ""))
    return jsonify({"ok": True})


@bp.route("/reunioes/<int:reuniao_id>/sincronizar", methods=["POST"])
def api_reuniao_sincronizar(reuniao_id):
    try:
        msg = sincronizar_presencas(reuniao_id)
        return jsonify({"ok": True, "message": msg})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@bp.route("/reunioes/configurar-forms", methods=["POST"])
def api_reunioes_forms():
    data = request.get_json(silent=True) or {}
    salvar_link_forms_presenca(data.get("sheets_presenca_url", ""))
    return jsonify({"ok": True})


@bp.route("/presencas/<int:reuniao_id>", methods=["GET", "POST"])
def api_presencas(reuniao_id):
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        presentes = [str(x) for x in data.get("presentes", [])]
        justificadas = [str(x) for x in data.get("justificadas", [])]
        lancar_presencas_reuniao(reuniao_id, presentes, justificadas)
        return jsonify({"ok": True, "message": "Presenças registradas."})
    return jsonify({
        "reuniao": _row_to_dict(buscar_reuniao(reuniao_id)),
        "presencas": _rows_to_list(listar_presencas_reuniao(reuniao_id)),
    })


@bp.route("/temas", methods=["GET", "POST"])
def api_temas():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        criar_tema(
            data.get("titulo", ""),
            data.get("data_aviso", ""),
            data.get("data_limite", ""),
            [int(x) for x in data.get("padrinho_ids", [])],
        )
        return jsonify({"ok": True}), 201
    ctx = montar_contexto_temas()
    return jsonify({
        "temas": [
            {"tema": _row_to_dict(item["tema"]), "padrinhos": _rows_to_list(item["padrinhos"])}
            for item in ctx["temas"]
        ],
        "padrinhos": _rows_to_list(ctx["padrinhos"]),
        "today": ctx["today"],
        "sheets_inscricoes_url": ctx["sheets_inscricoes_url"],
        "sugestao_vagas": ctx["sugestao_vagas"],
        "ultimo_prazo": ctx["ultimo_prazo"],
    })


@bp.route("/temas/<int:tema_id>", methods=["PUT", "DELETE"])
def api_tema_item(tema_id):
    if request.method == "DELETE":
        excluir_tema(tema_id)
        return jsonify({"ok": True})
    data = request.get_json(silent=True) or {}
    editar_tema(
        tema_id,
        data.get("titulo", ""),
        data.get("data_aviso", ""),
        data.get("data_limite", ""),
        [int(x) for x in data.get("padrinho_ids", [])],
    )
    return jsonify({"ok": True})


@bp.route("/temas/<int:tema_id>/entregue", methods=["POST"])
def api_tema_entregue(tema_id):
    data = request.get_json(silent=True) or {}
    msg, cat = registrar_entrega(tema_id, data.get("data_entrega", date.today().isoformat()))
    return jsonify({"ok": True, "message": msg, "category": cat})


@bp.route("/temas/<int:tema_id>/nao-entregue", methods=["POST"])
def api_tema_nao_entregue(tema_id):
    registrar_nao_entrega(tema_id)
    return jsonify({"ok": True, "message": "Tema marcado como não entregue."})


@bp.route("/temas/configurar-inscricoes", methods=["POST"])
def api_temas_config():
    data = request.get_json(silent=True) or {}
    salvar_link_inscricoes(data.get("sheets_inscricoes_url", ""))
    return jsonify({"ok": True})


@bp.route("/temas/sincronizar", methods=["POST"])
def api_temas_sincronizar():
    try:
        msg = sincronizar_responsaveis()
        return jsonify({"ok": True, "message": msg})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@bp.route("/match", methods=["GET"])
def api_match():
    ctx = montar_contexto_match()
    return jsonify({
        "dados": [
            {"padrinho": _row_to_dict(item["padrinho"]), "calouros": _rows_to_list(item["calouros"])}
            for item in ctx["dados"]
        ],
        "total_matches": ctx["total_matches"],
        "total_calouros": ctx["total_calouros"],
        "total_padrinhos": ctx["total_padrinhos"],
    })


@bp.route("/match/rodar", methods=["POST"])
def api_match_rodar():
    total = gerar_e_confirmar_match()
    return jsonify({"ok": True, "total": total})


@bp.route("/match/resetar", methods=["POST"])
def api_match_resetar():
    resetar_match()
    return jsonify({"ok": True})


@bp.route("/advertencias", methods=["GET", "POST"])
def api_advertencias():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        padrinho_id = data.get("padrinho_id")
        motivo = str(data.get("motivo", "")).strip()
        tipo = data.get("tipo", "vermelho")
        if tipo not in ("amarelo", "vermelho"):
            tipo = "vermelho"
        emitir_advertencia_manual(padrinho_id, motivo, tipo)
        registrar_log("ADVERTENCIA_MANUAL", f"Advertência manual ({tipo}) para padrinho ID {padrinho_id}: {motivo}")
        return jsonify({"ok": True}), 201

    return jsonify({
        "advertencias": _rows_to_list(advertencia_repository.listar_com_padrinho()),
        "padrinhos": _rows_to_list(get_todos_padrinhos()),
        "total_reunioes": contar_reunioes(),
    })


@bp.route("/advertencias/<int:advertencia_id>", methods=["DELETE"])
def api_advertencia_excluir(advertencia_id):
    padrinho_id = advertencia_repository.buscar_padrinho_id(advertencia_id)
    excluir_adv_registro(advertencia_id)
    registrar_log("EXCLUSAO_ADVERTENCIA", f"Advertência ID {advertencia_id} removida (padrinho ID {padrinho_id}).")
    return jsonify({"ok": True})


@bp.route("/relatorio", methods=["GET"])
def api_relatorio():
    ctx = montar_contexto_relatorio_geral()
    dados = []
    for d in ctx["dados"]:
        dados.append({
            "padrinho": _row_to_dict(d["padrinho"]),
            "total_reunioes": d["total_reunioes"],
            "total_presentes": d["total_presentes"],
            "amarelos": d["amarelos"],
            "vermelhos": d["vermelhos"],
            "status": d["status"],
        })
    return jsonify({"dados": dados, "stats": ctx["stats"]})


@bp.route("/inicio", methods=["GET"])
def api_inicio():
    return jsonify({
        "sheets_padrinhos_url": get_config("sheets_padrinhos_url", ""),
        "sheets_calouros_url": get_config("sheets_calouros_url", ""),
        "total_padrinhos": padrinho_repository.contar_ativos(),
        "total_calouros": match_repository.contar_calouros(),
    })


@bp.route("/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        config = {
            "semestre": str(data.get("semestre", "2026/1")).strip(),
            "professor_coordenador": str(data.get("professor_coordenador", "")).strip(),
            "programa": str(data.get("programa", "")).strip(),
            "instituicao": str(data.get("instituicao", "")).strip(),
            "total_reunioes": int(data.get("total_reunioes", 3)),
            "data_inicio": str(data.get("data_inicio", "")).strip(),
            "data_fim": str(data.get("data_fim", "")).strip(),
            "coordenadora_geral": str(data.get("coordenadora_geral", "")).strip(),
            "coordenadores": [str(n).strip() for n in (data.get("coordenadores") or []) if str(n).strip()],
        }
        salvar_config_semestre(config)
        registrar_log("ALTERACAO_CONFIG", f"Configurações do semestre {config['semestre']} atualizadas.")
        return jsonify({"ok": True, "config_semestre": config})

    return jsonify({
        "config_semestre": get_config_semestre(),
        "total_reunioes": contar_reunioes(),
    })


@bp.route("/logs", methods=["GET", "DELETE"])
def api_logs():
    conn = get_conn()
    if request.method == "DELETE":
        conn.execute("DELETE FROM logs")
        conn.commit()
        conn.close()
        registrar_log("LOGS_LIMPOS", "Logs de auditoria apagados pelo coordenador.")
        return jsonify({"ok": True})
    lista = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"logs": _rows_to_list(lista)})
