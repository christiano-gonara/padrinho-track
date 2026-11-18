from flask import Blueprint, flash, redirect, render_template, request

from services.presenca_service import (
    buscar_reuniao,
    formatar_mensagem_importacao,
    importar_presencas_upload,
    lancar_presencas_reuniao,
    listar_presencas_reuniao,
)


bp = Blueprint("presencas", __name__)


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
