from flask import Blueprint, flash, redirect, render_template, request

from models import get_todos_padrinhos
from services.padrinho_service import (
    cadastrar_novo_padrinho,
    editar_padrinho as editar_padrinho_service,
    excluir_padrinho as excluir_padrinho_service,
    listar_padrinhos_com_status,
    montar_contexto_padrinho_detalhe,
    redistribuir_padrinho,
)


bp = Blueprint("padrinhos", __name__)


@bp.route("/padrinhos")
def padrinhos():
    """Lista padrinhos com status calculado."""
    return render_template("pages/padrinhos.html", padrinhos=listar_padrinhos_com_status())


@bp.route("/padrinhos/novo", methods=["GET", "POST"])
def novo_padrinho():
    """Cadastra padrinho manualmente pela interface."""
    if request.method == "POST":
        sucesso, msg = cadastrar_novo_padrinho(
            request.form["nome"],
            request.form["matricula"],
            request.form.get("email", ""),
            request.form.get("telefone", ""),
            request.form.get("turno", ""),
        )
        flash(msg, "success" if sucesso else "error")
        if sucesso:
            return redirect("/padrinhos")
    return render_template("pages/padrinhos.html", padrinhos=get_todos_padrinhos())


@bp.route("/padrinhos/<int:padrinho_id>")
def padrinho_detalhe(padrinho_id):
    """Mostra histórico, advertências e calouros vinculados a um padrinho."""
    return render_template("pages/padrinho_detalhe.html", **montar_contexto_padrinho_detalhe(padrinho_id))


@bp.route("/padrinhos/<int:padrinho_id>/redistribuir", methods=["POST"])
def padrinho_redistribuir(padrinho_id):
    """Redistribui calouros e remove/desativa um padrinho."""
    redistribuir_padrinho(padrinho_id, request.form.items())
    flash("Padrinho removido do programa. Calouros redistribuídos.", "success")
    return redirect("/padrinhos")


@bp.route("/padrinhos/<int:padrinho_id>/editar", methods=["POST"])
def editar_padrinho(padrinho_id):
    """Recebe formulário de edição de padrinho."""
    editar_padrinho_service(padrinho_id, request.form)
    flash("Padrinho atualizado.", "success")
    return redirect(f"/padrinhos/{padrinho_id}")


@bp.route("/padrinhos/<int:padrinho_id>/excluir", methods=["POST"])
def excluir_padrinho(padrinho_id):
    """Remove/desativa um padrinho pelo painel."""
    excluir_padrinho_service(padrinho_id)
    flash("Padrinho removido do programa.", "success")
    return redirect("/padrinhos")
