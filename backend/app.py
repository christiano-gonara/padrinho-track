"""Monta a aplicação Flask e liga os blueprints de cada área.

Este arquivo cuida de três coisas: configurar o app, registrar as rotas de
login/logout e dizer quais URLs abrem sem sessão. O resto mora em backend/routes/.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from flask import Flask, jsonify, redirect, render_template, request, session, url_for  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from backend.database import init_db  # noqa: E402  (precisa do .env já carregado)
from backend.models import abreviar_nome, registrar_log  # noqa: E402
from backend.routes.advertencias import bp as advertencias_bp  # noqa: E402
from backend.routes.api import bp as api_bp  # noqa: E402
from backend.routes.configuracoes import bp as configuracoes_bp  # noqa: E402
from backend.routes.dashboard import bp as dashboard_bp  # noqa: E402
from backend.routes.inicio import bp as inicio_bp  # noqa: E402
from backend.routes.match import bp as match_bp  # noqa: E402
from backend.routes.padrinhos import bp as padrinhos_bp  # noqa: E402
from backend.routes.relatorios import bp as relatorios_bp  # noqa: E402
from backend.routes.reunioes import bp as reunioes_bp  # noqa: E402
from backend.routes.temas import bp as temas_bp  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"

app = Flask(
    __name__,
    template_folder=str(WEB_DIR / "templates"),
    static_folder=str(WEB_DIR / "static"),
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

_SECRET_KEY = os.environ.get("SECRET_KEY", "")
_APP_PASS = os.environ.get("APP_PASSWORD", "")
if not _SECRET_KEY or not _APP_PASS:
    raise RuntimeError(
        "Defina SECRET_KEY e APP_PASSWORD no arquivo .env antes de iniciar o servidor."
    )
app.secret_key = _SECRET_KEY

with app.app_context():
    init_db()

# Blueprints são grupos de rotas separados por domínio. O backend/app.py só monta
# a aplicação; cada arquivo em backend/routes/ cuida de uma área.
for _bp in (
    api_bp,
    dashboard_bp,
    advertencias_bp,
    configuracoes_bp,
    inicio_bp,
    relatorios_bp,
    reunioes_bp,
    temas_bp,
    padrinhos_bp,
    match_bp,
):
    app.register_blueprint(_bp)

app.jinja_env.filters["abreviar"] = abreviar_nome

# Rotas que abrem sem sessão: a apresentação, o login e os arquivos estáticos.
ROTAS_PUBLICAS = {"dashboard.landing", "login", "static", "api.auth_login", "api.auth_me", "api.auth_logout"}


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Registra erros inesperados para facilitar suporte e diagnóstico."""
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Erro inesperado")
    try:
        registrar_log("ERRO_SISTEMA", f"{type(error).__name__}: {error}")
    except Exception:
        pass
    return "Erro interno no servidor.", 500


@app.template_filter("databr")
def databr(value):
    """Formata datas YYYY-MM-DD para DD/MM nos templates Jinja."""
    if not value:
        return "—"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m")
    except Exception:
        return value


_APP_USER = os.environ.get("APP_USERNAME", "admin")


@app.before_request
def require_login():
    """Protege as rotas internas e libera a apresentação, o login e os estáticos."""
    if request.endpoint not in ROTAS_PUBLICAS and not session.get("logged_in"):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Não autenticado."}), 401
        return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Exibe o login e valida usuário/senha configurados no ambiente."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard.dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == _APP_USER and password == _APP_PASS:
            session["logged_in"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("dashboard.dashboard")
            return redirect(next_url)
        error = "Usuário ou senha inválidos."
    return render_template("pages/login.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    """Remove a sessão de login e volta para a tela de entrada."""
    session.clear()
    return redirect(url_for("login"))
