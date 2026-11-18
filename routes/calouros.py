from flask import Blueprint, render_template

from services.calouro_service import listar_calouros_com_match


bp = Blueprint("calouros", __name__)


@bp.route("/calouros")
def calouros():
    return render_template("pages/calouros.html", dados=listar_calouros_com_match())
