import os
from dotenv import load_dotenv
load_dotenv(override=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date, datetime
from database import init_db, get_conn
from models import (
    get_todos_padrinhos, get_padrinho, cadastrar_padrinho,
    get_todas_reunioes, criar_reuniao,
    lancar_presenca, get_presencas_reuniao, emitir_advertencias_falta,
    registrar_tema, registrar_entrega_tema, marcar_tema_nao_entregue,
    emitir_advertencia_manual, get_advertencias_padrinho,
    calcular_status, get_historico_padrinho, get_relatorio_geral,
    get_todos_temas, get_calouros_match_completo
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "padrinho-track-secret")

@app.template_filter('databr')
def databr(value):
    if not value:
        return "—"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m")
    except:
        return value

_APP_USER = os.environ.get("APP_USERNAME", "admin")
_APP_PASS = os.environ.get("APP_PASSWORD", "")

@app.before_request
def setup():
    init_db()

@app.before_request
def require_login():
    public = {"login", "static"}
    if request.endpoint not in public and not session.get("logged_in"):
        return redirect(url_for("login", next=request.path))

# ── Login / Logout ─────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == _APP_USER and password == _APP_PASS:
            session["logged_in"] = True
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "Usuário ou senha inválidos."
    return render_template("login.html", error=error)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ──────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    padrinhos = get_todos_padrinhos()
    dados = []
    for p in padrinhos:
        status = calcular_status(p["id"])
        dados.append({"padrinho": p, **status})

    conn = get_conn()
    proxima_reuniao = conn.execute(
        "SELECT * FROM reunioes ORDER BY data DESC LIMIT 1"
    ).fetchone()
    proximo_tema = conn.execute(
        "SELECT * FROM temas WHERE situacao = 'pendente' ORDER BY data_limite ASC LIMIT 1"
    ).fetchone()
    reunioes = conn.execute(
        "SELECT * FROM reunioes ORDER BY data ASC"
    ).fetchall()

    presencas_por_reuniao = []
    for r in reunioes:
        total = conn.execute(
            "SELECT COUNT(*) FROM presencas WHERE reuniao_id=?", (r["id"],)
        ).fetchone()[0]
        presentes = conn.execute(
            "SELECT COUNT(*) FROM presencas WHERE reuniao_id=? AND presente=1", (r["id"],)
        ).fetchone()[0]
        presencas_por_reuniao.append({
            "label": f"{r['data'][5:]}",
            "presentes": presentes,
            "ausentes": total - presentes,
        })
    conn.close()

    return render_template("dashboard.html",
        dados=dados,
        proxima_reuniao=proxima_reuniao,
        proximo_tema=proximo_tema,
        presencas_por_reuniao=presencas_por_reuniao,
    )

# ── Padrinhos ──────────────────────────────────────────────────────────────

@app.route("/padrinhos")
def padrinhos():
    lista = get_todos_padrinhos()
    return render_template("padrinhos.html", padrinhos=lista)

@app.route("/padrinhos/novo", methods=["GET", "POST"])
def novo_padrinho():
    if request.method == "POST":
        nome      = request.form["nome"].strip()
        matricula = request.form["matricula"].strip()
        email     = request.form.get("email", "").strip()
        telefone  = request.form.get("telefone", "").strip()
        turno     = request.form.get("turno", "").strip()
        try:
            cadastrar_padrinho(nome, matricula, email, telefone, turno)
            flash("Padrinho cadastrado com sucesso.", "success")
            return redirect(url_for("padrinhos"))
        except Exception:
            flash("Matrícula já cadastrada.", "error")
    return render_template("padrinhos.html", padrinhos=get_todos_padrinhos())

@app.route("/padrinhos/<int:padrinho_id>")
def padrinho_detalhe(padrinho_id):
    padrinho     = get_padrinho(padrinho_id)
    status       = calcular_status(padrinho_id)
    historico    = get_historico_padrinho(padrinho_id)
    advertencias = get_advertencias_padrinho(padrinho_id)
    return render_template("padrinho_detalhe.html",
        padrinho=padrinho,
        status=status,
        historico=historico,
        advertencias=advertencias
    )

# ── Reuniões ───────────────────────────────────────────────────────────────

@app.route("/reunioes")
def reunioes():
    lista = get_todas_reunioes()
    return render_template("reunioes.html", reunioes=lista)

@app.route("/reunioes/nova", methods=["POST"])
def nova_reuniao():
    data      = request.form["data"]
    tema      = request.form.get("tema", "").strip()
    descricao = request.form.get("descricao", "").strip()
    criar_reuniao(data, tema, descricao)
    flash("Reunião criada.", "success")
    return redirect(url_for("reunioes"))

# ── Presenças ──────────────────────────────────────────────────────────────

@app.route("/presencas/<int:reuniao_id>", methods=["GET", "POST"])
def presencas(reuniao_id):
    if request.method == "POST":
        padrinhos = get_todos_padrinhos()
        for p in padrinhos:
            pid         = str(p["id"])
            presente    = 1 if pid in request.form.getlist("presentes") else 0
            justificada = 1 if pid in request.form.getlist("justificadas") else 0
            lancar_presenca(reuniao_id, p["id"], presente, justificada)
        emitir_advertencias_falta(reuniao_id)
        flash("Presenças registradas. Advertências automáticas emitidas.", "success")
        return redirect(url_for("reunioes"))

    lista = get_presencas_reuniao(reuniao_id)
    return render_template("presencas.html", presencas=lista, reuniao_id=reuniao_id)

# ── Temas ──────────────────────────────────────────────────────────────────

@app.route("/temas")
def temas():
    lista     = get_todos_temas()
    padrinhos = get_todos_padrinhos()
    return render_template("temas.html", temas=lista, padrinhos=padrinhos, today=date.today().isoformat())

@app.route("/temas/novo", methods=["POST"])
def novo_tema():
    titulo       = request.form["titulo"].strip()
    data_aviso   = request.form.get("data_aviso", "")
    data_limite  = request.form["data_limite"]
    padrinho_ids = request.form.getlist("padrinho_ids")
    registrar_tema(titulo, data_aviso, data_limite, padrinho_ids)
    flash("Tema registrado.", "success")
    return redirect(url_for("temas"))

@app.route("/temas/<int:tema_id>/entregue", methods=["POST"])
def tema_entregue(tema_id):
    data_entrega = request.form.get("data_entrega", date.today().isoformat())
    situacao = registrar_entrega_tema(tema_id, data_entrega)
    mensagens = {
        "entregue":     ("Tema entregue no prazo.", "success"),
        "atraso":       ("Tema entregue com atraso — amarelo emitido.", "error"),
        "nao_entregue": ("Tema não entregue — vermelho emitido.", "error"),
    }
    msg, cat = mensagens.get(situacao, ("Status atualizado.", "success"))
    flash(msg, cat)
    return redirect(url_for("temas"))

@app.route("/temas/<int:tema_id>/nao_entregue", methods=["POST"])
def tema_nao_entregue(tema_id):
    marcar_tema_nao_entregue(tema_id)
    flash("Tema não entregue — vermelho emitido automaticamente.", "error")
    return redirect(url_for("temas"))

# ── Advertências ───────────────────────────────────────────────────────────

@app.route("/advertencias")
def advertencias():
    conn = get_conn()
    lista = conn.execute("""
        SELECT a.*, p.nome AS padrinho_nome
        FROM advertencias a
        JOIN padrinhos p ON p.id = a.padrinho_id
        ORDER BY a.data DESC
    """).fetchall()
    conn.close()
    padrinhos = get_todos_padrinhos()
    return render_template("advertencias.html", advertencias=lista, padrinhos=padrinhos)

@app.route("/advertencias/manual", methods=["POST"])
def advertencia_manual():
    padrinho_id = request.form["padrinho_id"]
    motivo      = request.form["motivo"].strip()
    emitir_advertencia_manual(padrinho_id, motivo)
    flash("Advertência manual registrada.", "error")
    return redirect(url_for("advertencias"))

# ── Relatório ──────────────────────────────────────────────────────────────

@app.route("/relatorio")
def relatorio():
    dados = get_relatorio_geral()
    return render_template("relatorio.html", dados=dados)


@app.route("/relatorio/pdf")
def exportar_pdf_acg():
    from models import gerar_pdf_acg
    from flask import send_file
    import io
    pdf_bytes = gerar_pdf_acg()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="relatorio_acg.pdf"
    )

@app.route("/relatorio/exportar")
def exportar_relatorio():
    from models import exportar_relatorio_csv
    from flask import send_file
    import os
    caminho = exportar_relatorio_csv("instance/relatorio_acg.csv")
    return send_file(
        os.path.abspath(caminho),
        mimetype="text/csv",
        as_attachment=True,
        download_name="relatorio_acg.csv"
    )

# ── Calouros ───────────────────────────────────────────────────────────────

@app.route("/calouros")
def calouros():
    dados = get_calouros_match_completo()
    return render_template("calouros.html", dados=dados)

# ── Configurações ──────────────────────────────────────────────────────────

@app.route("/config", methods=["GET", "POST"])
def configuracoes():
    if request.method == "POST":
        limite = request.form.get("limite_amarelos", "2")
        conn = get_conn()
        conn.execute(
            "UPDATE config SET valor=? WHERE chave='limite_amarelos'",
            (limite,)
        )
        conn.commit()
        conn.close()
        flash("Configurações salvas.", "success")
        return redirect(url_for("configuracoes"))
    from models import get_config
    limite_atual = get_config("limite_amarelos", "2")
    return render_template("config.html", limite_amarelos=limite_atual)

# ── CRUD Padrinhos ─────────────────────────────────────────────────────────

@app.route("/padrinhos/<int:padrinho_id>/editar", methods=["POST"])
def editar_padrinho(padrinho_id):
    from models import editar_padrinho as _editar
    _editar(
        padrinho_id,
        request.form["nome"].strip(),
        request.form["matricula"].strip(),
        request.form.get("email", "").strip(),
        request.form.get("telefone", "").strip(),
        request.form.get("turno", "").strip(),
    )
    flash("Padrinho atualizado.", "success")
    return redirect(url_for("padrinho_detalhe", padrinho_id=padrinho_id))

@app.route("/padrinhos/<int:padrinho_id>/excluir", methods=["POST"])
def excluir_padrinho(padrinho_id):
    from models import excluir_padrinho as _excluir
    _excluir(padrinho_id)
    flash("Padrinho removido do programa.", "success")
    return redirect(url_for("padrinhos"))

# ── CRUD Advertências ──────────────────────────────────────────────────────

@app.route("/advertencias/<int:advertencia_id>/excluir", methods=["POST"])
def excluir_advertencia(advertencia_id):
    from models import excluir_advertencia as _excluir
    conn = get_conn()
    adv = conn.execute("SELECT padrinho_id FROM advertencias WHERE id=?", (advertencia_id,)).fetchone()
    conn.close()
    padrinho_id = adv["padrinho_id"] if adv else None
    _excluir(advertencia_id)
    flash("Advertência removida.", "success")
    if padrinho_id:
        return redirect(url_for("padrinho_detalhe", padrinho_id=padrinho_id))
    return redirect(url_for("advertencias"))

# ── CRUD Reuniões ──────────────────────────────────────────────────────────

@app.route("/reunioes/<int:reuniao_id>/excluir", methods=["POST"])
def excluir_reuniao(reuniao_id):
    from models import excluir_reuniao as _excluir
    _excluir(reuniao_id)
    flash("Reunião removida.", "success")
    return redirect(url_for("reunioes"))

# ── CRUD Temas ─────────────────────────────────────────────────────────────

@app.route("/temas/<int:tema_id>/excluir", methods=["POST"])
def excluir_tema(tema_id):
    from models import excluir_tema as _excluir
    _excluir(tema_id)
    flash("Tema removido.", "success")
    return redirect(url_for("temas"))

# ── Relatórios separados ───────────────────────────────────────────────────

@app.route("/relatorio/aptos")
def relatorio_aptos():
    from models import get_relatorio_aptos
    dados = get_relatorio_aptos()
    return render_template("relatorio_aptos.html", dados=dados)

@app.route("/relatorio/vermelhos")
def relatorio_vermelhos():
    from models import get_relatorio_vermelhos
    dados = get_relatorio_vermelhos()
    return render_template("relatorio_vermelhos.html", dados=dados)

@app.route("/relatorio/aptos/exportar")
def exportar_aptos():
    from models import exportar_aptos_csv
    from flask import send_file
    import os
    caminho = exportar_aptos_csv()
    return send_file(os.path.abspath(caminho), mimetype="text/csv",
                     as_attachment=True, download_name="relatorio_aptos.csv")

@app.route("/relatorio/vermelhos/exportar")
def exportar_vermelhos():
    from models import exportar_vermelhos_csv
    from flask import send_file
    import os
    caminho = exportar_vermelhos_csv()
    return send_file(os.path.abspath(caminho), mimetype="text/csv",
                     as_attachment=True, download_name="relatorio_vermelhos.csv")

# ── Importação CSV ─────────────────────────────────────────────────────────

@app.route("/presencas/<int:reuniao_id>/importar", methods=["GET", "POST"])
def importar_presencas(reuniao_id):
    from models import importar_presencas_csv
    import os, tempfile

    conn = get_conn()
    reuniao = conn.execute("SELECT * FROM reunioes WHERE id=?", (reuniao_id,)).fetchone()
    conn.close()

    if request.method == "POST":
        arquivo = request.files.get("csv_file")
        if not arquivo or not arquivo.filename.endswith(".csv"):
            flash("Envie um arquivo CSV válido.", "error")
            return redirect(request.url)

        tmp_path = os.path.join(tempfile.gettempdir(), f"presenca_{reuniao_id}.csv")
        arquivo.save(tmp_path)
        resultado = importar_presencas_csv(tmp_path, reuniao_id)

        try:
            os.unlink(tmp_path)
        except Exception:
            pass

        if "erro" in resultado:
            flash(resultado["erro"], "error")
        else:
            msg = f"{resultado['processados']} presenças importadas."
            if resultado["nao_encontrados"]:
                msg += f" Matrículas não encontradas: {', '.join(resultado['nao_encontrados'])}"
            flash(msg, "success")
        return redirect(url_for("reunioes"))

    return render_template("importar_presencas.html", reuniao=reuniao)

# ── Inicialização ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)