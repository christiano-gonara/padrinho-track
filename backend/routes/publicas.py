"""Rotas públicas: a página de apresentação, que abre sem login."""

from flask import Blueprint, redirect, render_template, session, url_for

REPOSITORIO = "https://github.com/christiano-gonara/padrinho-track"

bp = Blueprint("publicas", __name__)


@bp.route("/")
def landing():
    """Apresenta o programa para quem ainda não entrou."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard.dashboard"))
    return render_template(
        "pages/landing.html",
        estatico=False,
        repositorio=REPOSITORIO,
    )
