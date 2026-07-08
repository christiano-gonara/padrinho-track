import os
from dotenv import load_dotenv
load_dotenv(override=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.exceptions import HTTPException
from datetime import date, datetime
from database import init_db, get_conn
from models import (
    get_todos_padrinhos,
    registrar_log,
    abreviar_nome, get_config_semestre, get_config, set_config, contar_reunioes,
)
from integrations.importers import importar_calouros_sheets, importar_padrinhos_sheets
from services.status_service import calcular_todos_status, emitir_advertencia_manual
from routes.relatorios import bp as relatorios_bp
from routes.reunioes import bp as reunioes_bp
from routes.presencas import bp as presencas_bp
from routes.temas import bp as temas_bp
from routes.padrinhos import bp as padrinhos_bp
from routes.calouros import bp as calouros_bp
from routes.match import bp as match_bp
from repositories import (
    advertencia_repository,
    calouro_repository,
    padrinho_repository,
    reuniao_repository,
    tema_repository,
)

# Instancia principal do Flask. Ela representa a aplicação web inteira.
# Em JavaScript/Express seria parecido com `const app = express()`.
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

CONFIG = get_config_semestre()

_SECRET_KEY = os.environ.get("SECRET_KEY", "")
_APP_PASS = os.environ.get("APP_PASSWORD", "")
if not _SECRET_KEY or not _APP_PASS:
    raise RuntimeError(
        "Defina SECRET_KEY e APP_PASSWORD no arquivo .env antes de iniciar o servidor."
    )
app.secret_key = _SECRET_KEY

with app.app_context():
    init_db()

# Blueprints são grupos de rotas separados por domínio. Assim o app.py fica
# responsável por montar a aplicação, e cada arquivo em routes/ cuida de uma área.
app.register_blueprint(relatorios_bp)
app.register_blueprint(reunioes_bp)
app.register_blueprint(presencas_bp)
app.register_blueprint(temas_bp)
app.register_blueprint(padrinhos_bp)
app.register_blueprint(calouros_bp)
app.register_blueprint(match_bp)

app.jinja_env.filters['abreviar'] = abreviar_nome


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

@app.template_filter('databr')
def databr(value):
    """Formata datas YYYY-MM-DD para DD/MM nos templates Jinja."""
    if not value:
        return "—"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m")
    except:
        return value

_APP_USER = os.environ.get("APP_USERNAME", "admin")

@app.before_request
def require_login():
    """Protege as rotas internas e libera apenas login e arquivos estáticos."""
    public = {"login", "static"}
    if request.endpoint not in public and not session.get("logged_in"):
        return redirect(url_for("login", next=request.path))

# ── Login / Logout ─────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    """Exibe o login e valida usuário/senha configurados no ambiente."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == _APP_USER and password == _APP_PASS:
            session["logged_in"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("dashboard")
            return redirect(next_url)
        error = "Usuário ou senha inválidos."
    return render_template("pages/login.html", error=error)

@app.route("/logout", methods=["POST"])
def logout():
    """Remove a sessão de login e volta para a tela de entrada."""
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ──────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Monta a visão inicial com status dos padrinhos e gráficos resumidos."""
    padrinhos = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    dados = [{"padrinho": p, **todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})} for p in padrinhos]

    proxima_reuniao = reuniao_repository.buscar_ultima()
    proximo_tema = tema_repository.buscar_proximo_pendente()
    reunioes = reuniao_repository.listar_todas_asc()
    ppr_rows = reuniao_repository.contar_presencas_por_reuniao()
    ppr_map = {r["reuniao_id"]: r for r in ppr_rows}
    presencas_por_reuniao = []
    for r in reunioes:
        ppr = ppr_map.get(r["id"])
        presentes = ppr["presentes"] if ppr else 0
        total = ppr["total"] if ppr else 0
        presencas_por_reuniao.append({
            "label": f"{r['data'][5:]}",
            "presentes": presentes,
            "ausentes": total - presentes,
        })

    return render_template("pages/dashboard.html",
        dados=dados,
        proxima_reuniao=proxima_reuniao,
        proximo_tema=proximo_tema,
        presencas_por_reuniao=presencas_por_reuniao,
    )

# ── Advertências ───────────────────────────────────────────────────────────

@app.route("/advertencias")
def advertencias():
    """Lista advertências registradas e dados auxiliares para ações manuais."""
    lista = advertencia_repository.listar_com_padrinho()
    padrinhos = get_todos_padrinhos()
    total_reunioes = contar_reunioes()
    return render_template("pages/advertencias.html", advertencias=lista, padrinhos=padrinhos, total_reunioes=total_reunioes)

@app.route("/advertencias/manual", methods=["POST"])
def advertencia_manual():
    """Registra uma advertência manual para um padrinho."""
    padrinho_id = request.form["padrinho_id"]
    motivo      = request.form["motivo"].strip()
    tipo        = request.form.get("tipo", "vermelho")
    if tipo not in ("amarelo", "vermelho"):
        tipo = "vermelho"
    emitir_advertencia_manual(padrinho_id, motivo, tipo)
    registrar_log("ADVERTENCIA_MANUAL", f"Advertência manual ({tipo}) para padrinho ID {padrinho_id}: {motivo}")
    flash("Advertência manual registrada.", "error")
    return redirect(url_for("advertencias"))

# ── Configurações ──────────────────────────────────────────────────────────

@app.route("/config", methods=["GET", "POST"])
def configuracoes():
    """Exibe e salva as configurações gerais do semestre."""
    global CONFIG
    from models import salvar_config_semestre
    if request.method == "POST":
        coordenadores_raw = request.form.get("coordenadores", "")
        coordenadores = [n.strip() for n in coordenadores_raw.splitlines() if n.strip()]
        cfg = {
            "semestre": request.form.get("semestre", "2026/1").strip(),
            "professor_coordenador": request.form.get("professor_coordenador", "").strip(),
            "programa": request.form.get("programa", "").strip(),
            "instituicao": request.form.get("instituicao", "").strip(),
            "total_reunioes": int(request.form.get("total_reunioes", 3)),
            "data_inicio": request.form.get("data_inicio", "").strip(),
            "data_fim": request.form.get("data_fim", "").strip(),
            "coordenadora_geral": request.form.get("coordenadora_geral", "").strip(),
            "coordenadores": coordenadores,
        }
        salvar_config_semestre(cfg)
        CONFIG = get_config_semestre()
        registrar_log("ALTERACAO_CONFIG", f"Configurações do semestre {cfg['semestre']} atualizadas.")
        flash("Configurações salvas.", "success")
        return redirect(url_for("configuracoes"))
    return render_template("pages/config.html",
        config_semestre=CONFIG,
        total_reunioes=contar_reunioes(),
    )

# ── CRUD Advertências ──────────────────────────────────────────────────────

@app.route("/advertencias/<int:advertencia_id>/excluir", methods=["POST"])
def excluir_advertencia(advertencia_id):
    """Remove uma advertência e volta para o detalhe do padrinho quando possível."""
    from models import excluir_advertencia as _excluir
    padrinho_id = advertencia_repository.buscar_padrinho_id(advertencia_id)
    _excluir(advertencia_id)
    registrar_log("EXCLUSAO_ADVERTENCIA", f"Advertência ID {advertencia_id} removida (padrinho ID {padrinho_id}).")
    flash("Advertência removida.", "success")
    if padrinho_id:
        return redirect(f"/padrinhos/{padrinho_id}")
    return redirect(url_for("advertencias"))

# ── Backup do banco ───────────────────────────────────────────────────────

@app.route("/config/backup-db")
def backup_db():
    """Baixa uma cópia do banco SQLite local."""
    from flask import send_file
    from database import DB_PATH
    from datetime import date as _date
    nome = f"mentoria_{_date.today().isoformat()}.db"
    registrar_log("BACKUP_DB", "Backup do banco exportado pelo coordenador.")
    return send_file(str(DB_PATH), as_attachment=True, download_name=nome)

# ── Logs de auditoria ─────────────────────────────────────────────────────

@app.route("/logs/limpar", methods=["POST"])
def logs_limpar():
    """Limpa os logs de auditoria do sistema."""
    conn = get_conn()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    registrar_log("LOGS_LIMPOS", "Logs de auditoria apagados pelo coordenador.")
    flash("Logs de auditoria apagados.", "success")
    return redirect(url_for("configuracoes"))

@app.route("/logs")
def logs():
    """Mostra os logs de auditoria em ordem recente."""
    conn = get_conn()
    lista = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages/logs.html", logs=lista)

# ── Início do Semestre ────────────────────────────────────────────────────

@app.route("/inicio")
def inicio_semestre():
    """Tela operacional para importar dados no começo do semestre."""
    total_padrinhos = padrinho_repository.contar_ativos()
    total_calouros = calouro_repository.contar_todos()
    sheets_padrinhos_url = get_config("sheets_padrinhos_url", "")
    sheets_calouros_url  = get_config("sheets_calouros_url", "")
    return render_template("pages/inicio_semestre.html",
        total_padrinhos=total_padrinhos,
        total_calouros=total_calouros,
        sheets_padrinhos_url=sheets_padrinhos_url,
        sheets_calouros_url=sheets_calouros_url,
    )

@app.route("/inicio/importar-padrinhos", methods=["POST"])
def inicio_importar_padrinhos():
    """Importa padrinhos de uma planilha vinculada ao Google Forms."""
    url = request.form.get("sheets_padrinhos_url", "").strip()
    if url:
        set_config("sheets_padrinhos_url", url)
    else:
        url = get_config("sheets_padrinhos_url", "")
    if not url:
        flash("Cole o link da planilha antes de importar.", "error")
        return redirect(url_for("inicio_semestre"))
    try:
        resultado = importar_padrinhos_sheets(url)
        msg = (f"{resultado['importados']} padrinho(s) importado(s). "
               f"{resultado['ignorados']} ignorado(s) (curso diferente). "
               f"{resultado['duplicatas']} duplicata(s).")
        registrar_log("IMPORTACAO_PADRINHOS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao importar: {e}", "error")
    return redirect(url_for("inicio_semestre"))

@app.route("/inicio/importar-calouros", methods=["POST"])
def inicio_importar_calouros():
    """Importa calouros de uma planilha vinculada ao Google Forms."""
    url = request.form.get("sheets_calouros_url", "").strip()
    if url:
        set_config("sheets_calouros_url", url)
    else:
        url = get_config("sheets_calouros_url", "")
    if not url:
        flash("Cole o link da planilha antes de importar.", "error")
        return redirect(url_for("inicio_semestre"))
    try:
        resultado = importar_calouros_sheets(url)
        msg = (f"{resultado['importados']} calouro(s) importado(s). "
               f"{resultado['ignorados']} ignorado(s) (curso diferente). "
               f"{resultado['duplicatas']} duplicata(s).")
        registrar_log("IMPORTACAO_CALOUROS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao importar: {e}", "error")
    return redirect(url_for("inicio_semestre"))

# ── Seed de demonstração ───────────────────────────────────────────────────

@app.route("/seed-exemplo")
def seed_exemplo():
    """Recria o banco com dados fictícios de demonstração."""
    if request.args.get("senha") != "PucMinas2026":
        return "Acesso negado.", 403
    conn1 = get_conn()
    conn1.execute(
        "TRUNCATE matches, calouros, presencas, advertencias,"
        " tema_padrinhos, temas, reunioes, padrinhos"
        " RESTART IDENTITY CASCADE"
    )
    conn1.commit()
    conn1.close()
    from scripts.seed_exemplo import seed
    seed()
    return redirect(url_for("dashboard"))


@app.route("/seed-real")
def seed_real():
    """Recria o banco local usando os scripts reais mantidos fora do Git."""
    import contextlib
    import io

    if request.args.get("senha") != "PucMinas2026":
        return "Acesso negado.", 403
    try:
        from scripts import seed as seed_mod
    except ImportError:
        return (
            "Arquivo scripts/seed.py não encontrado. "
            "Crie o seed real localmente; ele fica fora do git por conter dados sensíveis.",
            500,
        )

    conn = get_conn()
    for table in ("matches", "calouros", "presencas", "advertencias", "tema_padrinhos", "temas", "reunioes", "padrinhos"):
        conn.execute(f"DELETE FROM {table}")
    try:
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('matches','calouros','presencas','advertencias','temas','reunioes','padrinhos')"
        )
    except Exception:
        pass
    conn.commit()
    conn.close()

    with contextlib.redirect_stdout(io.StringIO()):
        if hasattr(seed_mod, "seed"):
            seed_mod.seed()
        else:
            if hasattr(seed_mod, "seed_padrinhos"):
                seed_mod.seed_padrinhos()
            if hasattr(seed_mod, "seed_temas"):
                seed_mod.seed_temas()

        try:
            from scripts import seed_calouros as seed_calouros_mod
        except ImportError:
            seed_calouros_mod = None
        if seed_calouros_mod:
            if hasattr(seed_calouros_mod, "seed"):
                seed_calouros_mod.seed()
            elif hasattr(seed_calouros_mod, "seed_calouros"):
                seed_calouros_mod.seed_calouros()

    registrar_log("SEED_REAL", "Seed real executado a partir de scripts/seed.py e scripts/seed_calouros.py.")
    flash("Seed real executado com sucesso.", "success")
    return redirect(url_for("dashboard"))

# ── Inicialização ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
