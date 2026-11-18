from datetime import date

from flask import Blueprint, Response, flash, redirect, render_template

from models import get_config_semestre
from services.match_service import (
    gerar_csv_lista_contatos,
    gerar_e_confirmar_match,
    listar_contatos_match,
    montar_contexto_match,
    resetar_match,
)


bp = Blueprint("match", __name__)


@bp.route("/match")
def match():
    """Mostra a tela de distribuição padrinho-calouro."""
    return render_template("pages/match.html", **montar_contexto_match())


@bp.route("/match/rodar", methods=["POST"])
def match_rodar():
    """Executa e grava um novo match automático."""
    total = gerar_e_confirmar_match()
    flash(f"{total} matches gerados e confirmados.", "success")
    return redirect("/match")


@bp.route("/match/resetar", methods=["POST"])
def match_resetar():
    """Apaga todos os matches atuais."""
    resetar_match()
    flash("Matches resetados.", "success")
    return redirect("/match")


@bp.route("/match/lista-contatos")
def match_lista_contatos():
    """Mostra lista imprimível de contatos do match."""
    return render_template(
        "pages/lista_contatos.html",
        rows=listar_contatos_match(),
        config=get_config_semestre(),
        hoje=date.today(),
    )


@bp.route("/match/exportar")
def match_exportar():
    """Exporta lista de contatos do match em CSV."""
    return Response(
        gerar_csv_lista_contatos(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=lista_contatos_match.csv"},
    )
