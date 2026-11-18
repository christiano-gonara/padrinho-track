from flask import Blueprint, flash, redirect, render_template, request

from backend.services.reuniao_service import (
    buscar_reuniao,
    criar_nova_reuniao,
    editar_reuniao as editar_reuniao_service,
    excluir_reuniao as excluir_reuniao_service,
    formatar_mensagem_importacao,
    importar_presencas_upload,
    lancar_presencas_reuniao,
    listar_presencas_reuniao,
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


@bp.route("/presencas/<int:reuniao_id>", methods=["GET", "POST"])
def presencas(reuniao_id):
    """Mostra ou salva presenças manuais de uma reunião."""
    if request.method == "POST":
        lancar_presencas_reuniao(
            reuniao_id,
            request.form.getlist("presentes"),
            request.form.getlist("justificadas"),
        )
        flash("Presenças registradas. Advertências automáticas emitidas.", "success")
        return redirect("/reunioes")

    return render_template(
        "pages/presencas.html",
        presencas=listar_presencas_reuniao(reuniao_id),
        reuniao=buscar_reuniao(reuniao_id),
        reuniao_id=reuniao_id,
    )


@bp.route("/presencas/<int:reuniao_id>/importar", methods=["GET", "POST"])
def importar_presencas(reuniao_id):
    """Importa presenças de uma reunião via upload de CSV."""
    reuniao = buscar_reuniao(reuniao_id)

    if request.method == "POST":
        resultado = importar_presencas_upload(request.files.get("csv_file"), reuniao_id)
        msg, categoria = formatar_mensagem_importacao(resultado)
        flash(msg, categoria)
        if categoria == "error" and msg == "Envie um arquivo CSV válido.":
            return redirect(request.url)
        return redirect("/reunioes")

    return render_template("pages/importar_presencas.html", reuniao=reuniao)
