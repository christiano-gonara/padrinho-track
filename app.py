from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_conn
from models import (
    get_todos_padrinhos, get_padrinho, cadastrar_padrinho,
    get_todas_reunioes, criar_reuniao,
    lancar_presenca, get_presencas_reuniao, emitir_advertencias_falta,
    registrar_tema, marcar_tema_entregue, marcar_tema_nao_entregue,
    emitir_advertencia_manual, get_advertencias_padrinho,
    calcular_status, get_historico_padrinho, get_relatorio_geral
)

app = Flask(__name__)
app.secret_key = "padrinho-track-secret"

@app.before_request
def setup():
    init_db()

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
        "SELECT * FROM temas WHERE entregue = 0 ORDER BY data_limite ASC LIMIT 1"
    ).fetchone()
    conn.close()

    return render_template("dashboard.html",
        dados=dados,
        proxima_reuniao=proxima_reuniao,
        proximo_tema=proximo_tema
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
        try:
            cadastrar_padrinho(nome, matricula, email)
            flash("Padrinho cadastrado com sucesso.", "success")
            return redirect(url_for("padrinhos"))
        except Exception:
            flash("Matrícula já cadastrada.", "error")
    return render_template("padrinhos.html", padrinhos=get_todos_padrinhos())

@app.route("/padrinhos/<int:padrinho_id>")
def padrinho_detalhe(padrinho_id):
    padrinho    = get_padrinho(padrinho_id)
    status      = calcular_status(padrinho_id)
    historico   = get_historico_padrinho(padrinho_id)
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
    conn = get_conn()
    lista = conn.execute("""
        SELECT t.*, p.nome AS padrinho_nome
        FROM temas t
        JOIN padrinhos p ON p.id = t.padrinho_id
        ORDER BY t.data_limite ASC
    """).fetchall()
    conn.close()
    padrinhos = get_todos_padrinhos()
    return render_template("temas.html", temas=lista, padrinhos=padrinhos)

@app.route("/temas/novo", methods=["POST"])
def novo_tema():
    titulo      = request.form["titulo"].strip()
    data_limite = request.form["data_limite"]
    padrinho_id = request.form["padrinho_id"]
    registrar_tema(titulo, data_limite, padrinho_id)
    flash("Tema registrado.", "success")
    return redirect(url_for("temas"))

@app.route("/temas/<int:tema_id>/entregue", methods=["POST"])
def tema_entregue(tema_id):
    marcar_tema_entregue(tema_id)
    flash("Tema marcado como entregue.", "success")
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

# ── Inicialização ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)