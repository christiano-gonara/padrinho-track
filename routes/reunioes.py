from flask import Blueprint, flash, redirect, render_template, request

from services.reuniao_service import (
    criar_nova_reuniao,
    editar_reuniao as editar_reuniao_service,
    excluir_reuniao as excluir_reuniao_service,
    montar_contexto_reunioes,
    salvar_link_forms_presenca,
    sincronizar_presencas,
)


bp = Blueprint("reunioes", __name__)


@bp.route("/reunioes")
def reunioes():
    """Mostra reuniões cadastradas e configuração do Forms de presença."""
    return render_template("pages/reunioes.html", **montar_contexto_reunioes())


@bp.route("/reunioes/<int:reuniao_id>/sincronizar", methods=["POST"])
def reuniao_sincronizar(reuniao_id):
    """Sincroniza presenças de uma reunião via Google Sheets."""
    try:
        flash(sincronizar_presencas(reuniao_id), "success")
    except Exception as e:
        flash(f"Erro ao sincronizar: {e}", "error")
    return redirect("/reunioes")


@bp.route("/reunioes/nova", methods=["POST"])
def nova_reuniao():
    """Cria uma reunião a partir do modal da interface."""
    criar_nova_reuniao(
        request.form["data"],
        request.form.get("tema", ""),
        request.form.get("descricao", ""),
    )
    flash("Reunião criada.", "success")
    return redirect("/reunioes")


@bp.route("/reunioes/configurar-forms", methods=["POST"])
def reunioes_configurar_forms():
    """Salva o link do Forms/Sheets de presença."""
    salvar_link_forms_presenca(request.form.get("sheets_presenca_url", ""))
    flash("Link salvo com sucesso.", "success")
    return redirect("/reunioes")


@bp.route("/reunioes/<int:reuniao_id>/excluir", methods=["POST"])
def excluir_reuniao(reuniao_id):
    """Remove uma reunião."""
    excluir_reuniao_service(reuniao_id)
    flash("Reunião removida.", "success")
    return redirect("/reunioes")


@bp.route("/reunioes/<int:reuniao_id>/editar", methods=["POST"])
def editar_reuniao(reuniao_id):
    """Atualiza uma reunião existente."""
    editar_reuniao_service(
        reuniao_id,
        request.form["data"],
        request.form.get("tema", ""),
        request.form.get("descricao", ""),
    )
    flash("Reunião atualizada.", "success")
    return redirect("/reunioes")
