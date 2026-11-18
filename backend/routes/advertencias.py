"""Advertências: listagem, emissão manual e exclusão."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.models import contar_reunioes, get_todos_padrinhos, registrar_log
from backend.models import excluir_advertencia as excluir_registro
from backend.repositories import advertencia_repository
from backend.services.status_service import emitir_advertencia_manual

bp = Blueprint("advertencias", __name__)


@bp.route("/advertencias")
def advertencias():
    """Lista advertências registradas e dados auxiliares para ações manuais."""
    lista = advertencia_repository.listar_com_padrinho()
    padrinhos = get_todos_padrinhos()
    total_reunioes = contar_reunioes()
    return render_template(
        "pages/advertencias.html",
        advertencias=lista,
        padrinhos=padrinhos,
        total_reunioes=total_reunioes,
    )


@bp.route("/advertencias/manual", methods=["POST"])
def advertencia_manual():
    """Registra uma advertência manual para um padrinho."""
    padrinho_id = request.form["padrinho_id"]
    motivo = request.form["motivo"].strip()
    tipo = request.form.get("tipo", "vermelho")
    if tipo not in ("amarelo", "vermelho"):
        tipo = "vermelho"
    emitir_advertencia_manual(padrinho_id, motivo, tipo)
    registrar_log(
        "ADVERTENCIA_MANUAL",
        f"Advertência manual ({tipo}) para padrinho ID {padrinho_id}: {motivo}",
    )
    flash("Advertência manual registrada.", "error")
    return redirect(url_for("advertencias.advertencias"))


@bp.route("/advertencias/<int:advertencia_id>/excluir", methods=["POST"])
def excluir_advertencia(advertencia_id):
    """Remove uma advertência e volta para o detalhe do padrinho quando possível."""
    padrinho_id = advertencia_repository.buscar_padrinho_id(advertencia_id)
    excluir_registro(advertencia_id)
    registrar_log(
        "EXCLUSAO_ADVERTENCIA",
        f"Advertência ID {advertencia_id} removida (padrinho ID {padrinho_id}).",
    )
    flash("Advertência removida.", "success")
    if padrinho_id:
        return redirect(f"/padrinhos/{padrinho_id}")
    return redirect(url_for("advertencias.advertencias"))
