from datetime import date

from flask import Blueprint, flash, redirect, render_template, request

from services.tema_service import (
    criar_tema,
    editar_tema as editar_tema_service,
    excluir_tema as excluir_tema_service,
    montar_contexto_temas,
    registrar_entrega,
    registrar_nao_entrega,
    salvar_link_inscricoes,
    sincronizar_responsaveis,
)


bp = Blueprint("temas", __name__)


@bp.route("/temas")
def temas():
    """Mostra cronograma de temas e responsáveis."""
    return render_template("pages/temas.html", **montar_contexto_temas())


@bp.route("/temas/configurar-inscricoes", methods=["POST"])
def temas_configurar_inscricoes():
    """Salva o link do Forms/Sheets de inscrição em temas."""
    salvar_link_inscricoes(request.form.get("sheets_inscricoes_url", ""))
    flash("Link salvo com sucesso.", "success")
    return redirect("/temas")


@bp.route("/temas/sincronizar", methods=["POST"])
def temas_sincronizar():
    """Sincroniza responsáveis por tema via Google Sheets."""
    try:
        flash(sincronizar_responsaveis(), "success")
    except Exception as e:
        flash(f"Erro ao sincronizar: {e}", "error")
    return redirect("/temas")


@bp.route("/temas/novo", methods=["POST"])
def novo_tema():
    """Cria um novo tema no cronograma."""
    criar_tema(
        request.form["titulo"],
        request.form.get("data_aviso", ""),
        request.form["data_limite"],
        request.form.getlist("padrinho_ids"),
    )
    flash("Tema registrado.", "success")
    return redirect("/temas")


@bp.route("/temas/<int:tema_id>/entregue", methods=["POST"])
def tema_entregue(tema_id):
    """Marca um tema como entregue."""
    data_entrega = request.form.get("data_entrega", date.today().isoformat())
    msg, categoria = registrar_entrega(tema_id, data_entrega)
    flash(msg, categoria)
    return redirect("/temas")


@bp.route("/temas/<int:tema_id>/nao_entregue", methods=["POST"])
def tema_nao_entregue(tema_id):
    """Marca um tema como não entregue."""
    registrar_nao_entrega(tema_id)
    flash("Tema não entregue — vermelho emitido automaticamente.", "error")
    return redirect("/temas")


@bp.route("/temas/<int:tema_id>/excluir", methods=["POST"])
def excluir_tema(tema_id):
    """Remove um tema."""
    excluir_tema_service(tema_id)
    flash("Tema removido.", "success")
    return redirect("/temas")


@bp.route("/temas/<int:tema_id>/editar", methods=["POST"])
def editar_tema(tema_id):
    """Atualiza um tema existente."""
    editar_tema_service(
        tema_id,
        request.form["titulo"],
        request.form.get("data_aviso", ""),
        request.form["data_limite"],
        request.form.getlist("padrinho_ids"),
    )
    flash("Tema atualizado.", "success")
    return redirect("/temas")
