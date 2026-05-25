import os
import sqlite3
from dotenv import load_dotenv
load_dotenv(override=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date, datetime
from database import init_db, get_conn
import math
from models import (
    get_todos_padrinhos, get_padrinho, cadastrar_padrinho,
    get_todas_reunioes, criar_reuniao,
    lancar_presenca, get_presencas_reuniao, emitir_advertencias_falta,
    registrar_tema, registrar_entrega_tema, marcar_tema_nao_entregue,
    emitir_advertencia_manual, get_advertencias_padrinho,
    calcular_status, get_historico_padrinho, get_relatorio_geral,
    get_todos_temas, get_calouros_match_completo, registrar_log,
    abreviar_nome, get_config_semestre, get_config,
    redistribuir_calouros,
)

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

app.jinja_env.filters['abreviar'] = abreviar_nome

@app.template_filter('databr')
def databr(value):
    if not value:
        return "—"
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m")
    except:
        return value

_APP_USER = os.environ.get("APP_USERNAME", "admin")

# @app.before_request
# def require_login():
#     public = {"login", "static"}
#     if request.endpoint not in public and not session.get("logged_in"):
#         return redirect(url_for("login", next=request.path))

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
            next_url = request.args.get("next", "")
            if not next_url.startswith("/"):
                next_url = url_for("dashboard")
            return redirect(next_url)
        error = "Usuário ou senha inválidos."
    return render_template("pages/login.html", error=error)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Dashboard ──────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    padrinhos = get_todos_padrinhos()
    limite = int(get_config("limite_amarelos", "2"))
    dados = []
    for p in padrinhos:
        status = calcular_status(p["id"], limite)
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

    ppr_rows = conn.execute("""
        SELECT reuniao_id,
               SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END) AS presentes,
               COUNT(*) AS total
        FROM presencas GROUP BY reuniao_id
    """).fetchall()
    conn.close()
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

# ── Padrinhos ──────────────────────────────────────────────────────────────

@app.route("/padrinhos")
def padrinhos():
    lista = get_todos_padrinhos()
    return render_template("pages/padrinhos.html", padrinhos=lista)

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
            registrar_log("CADASTRO_PADRINHO", f"Padrinho '{nome}' (matrícula {matricula}) cadastrado.")
            flash("Padrinho cadastrado com sucesso.", "success")
            return redirect(url_for("padrinhos"))
        except sqlite3.IntegrityError:
            flash("Matrícula já cadastrada.", "error")
    return render_template("pages/padrinhos.html", padrinhos=get_todos_padrinhos())

@app.route("/padrinhos/<int:padrinho_id>")
def padrinho_detalhe(padrinho_id):
    padrinho     = get_padrinho(padrinho_id)
    status       = calcular_status(padrinho_id)
    historico    = get_historico_padrinho(padrinho_id)
    advertencias = get_advertencias_padrinho(padrinho_id)
    conn = get_conn()
    calouros_match = conn.execute("""
        SELECT c.id, c.nome, c.telefone
        FROM matches m JOIN calouros c ON c.id = m.calouro_id
        WHERE m.padrinho_id = ?
        ORDER BY c.nome
    """, (padrinho_id,)).fetchall()
    todos_padrinhos = conn.execute(
        "SELECT id, nome FROM padrinhos WHERE ativo=1 AND id != ? ORDER BY nome",
        (padrinho_id,)
    ).fetchall()
    conn.close()
    return render_template("pages/padrinho_detalhe.html",
        padrinho=padrinho,
        status=status,
        historico=historico,
        advertencias=advertencias,
        calouros_match=calouros_match,
        todos_padrinhos=todos_padrinhos,
    )

@app.route("/padrinhos/<int:padrinho_id>/redistribuir", methods=["POST"])
def padrinho_redistribuir(padrinho_id):
    redistribuicao = {}
    for key, value in request.form.items():
        if key.startswith("calouro_"):
            calouro_id = int(key.split("_")[1])
            redistribuicao[calouro_id] = int(value) if value else None
    redistribuir_calouros(padrinho_id, redistribuicao)
    registrar_log("REMOCAO_PADRINHO", f"Padrinho ID {padrinho_id} removido do programa. Calouros redistribuídos.")
    flash("Padrinho removido do programa. Calouros redistribuídos.", "success")
    return redirect(url_for("padrinhos"))

# ── Reuniões ───────────────────────────────────────────────────────────────

@app.route("/reunioes")
def reunioes():
    lista = get_todas_reunioes()
    return render_template("pages/reunioes.html", reunioes=lista)

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
        presentes_ids = set(request.form.getlist("presentes"))
        justificadas_ids = set(request.form.getlist("justificadas"))
        conn = get_conn()
        for p in padrinhos:
            pid = str(p["id"])
            presente    = 1 if pid in presentes_ids else 0
            justificada = 1 if pid in justificadas_ids else 0
            conn.execute("""
                INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(reuniao_id, padrinho_id)
                DO UPDATE SET presente = excluded.presente, justificada = excluded.justificada
            """, (reuniao_id, p["id"], presente, justificada))
        conn.commit()
        conn.close()
        emitir_advertencias_falta(reuniao_id)
        registrar_log("LANCAMENTO_PRESENCA", f"Presenças lançadas para a reunião ID {reuniao_id}.")
        flash("Presenças registradas. Advertências automáticas emitidas.", "success")
        return redirect(url_for("reunioes"))

    lista = get_presencas_reuniao(reuniao_id)
    return render_template("pages/presencas.html", presencas=lista, reuniao_id=reuniao_id)

# ── Temas ──────────────────────────────────────────────────────────────────

@app.route("/temas")
def temas():
    lista     = get_todos_temas()
    padrinhos = get_todos_padrinhos()
    return render_template("pages/temas.html", temas=lista, padrinhos=padrinhos, today=date.today().isoformat())

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
    return render_template("pages/advertencias.html", advertencias=lista, padrinhos=padrinhos)

@app.route("/advertencias/manual", methods=["POST"])
def advertencia_manual():
    padrinho_id = request.form["padrinho_id"]
    motivo      = request.form["motivo"].strip()
    emitir_advertencia_manual(padrinho_id, motivo)
    registrar_log("ADVERTENCIA_MANUAL", f"Advertência manual para padrinho ID {padrinho_id}: {motivo}")
    flash("Advertência manual registrada.", "error")
    return redirect(url_for("advertencias"))

# ── Relatório ──────────────────────────────────────────────────────────────

@app.route("/relatorio")
def relatorio():
    dados = get_relatorio_geral()
    padrinhos_raw = get_todos_padrinhos()
    total = len(padrinhos_raw) or 1
    por_turno = {}
    n_fem = n_masc = n_prouni = n_bh = n_trabalha = 0
    for p in padrinhos_raw:
        turno = p["turno"] or "—"
        por_turno[turno] = por_turno.get(turno, 0) + 1
        if p["genero"] == "F":
            n_fem += 1
        elif p["genero"] == "M":
            n_masc += 1
        if p["prouni"]:
            n_prouni += 1
        if p["cidade_bh"]:
            n_bh += 1
        if p["trabalha"]:
            n_trabalha += 1
    stats = {
        "por_turno": por_turno,
        "pct_feminino": round(n_fem / total * 100),
        "pct_masculino": round(n_masc / total * 100),
        "pct_prouni": round(n_prouni / total * 100),
        "pct_bh": round(n_bh / total * 100),
        "pct_trabalha": round(n_trabalha / total * 100),
        "total": total,
    }
    return render_template("pages/relatorio.html", dados=dados, stats=stats)


@app.route("/relatorio/pdf")
def exportar_pdf_acg():
    from models import gerar_pdf_acg
    from flask import send_file
    import io
    pdf_bytes = gerar_pdf_acg()
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name="relatorio_acg.pdf")

@app.route("/relatorio/pdf/semestre")
def exportar_pdf_semestre():
    from models import gerar_pdf_resumo_semestre
    from flask import send_file
    import io
    pdf_bytes = gerar_pdf_resumo_semestre()
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name="resumo_semestre.pdf")

@app.route("/relatorio/pdf/graves")
def exportar_pdf_graves():
    from models import gerar_pdf_inaptos_graves
    from flask import send_file
    import io
    pdf_bytes = gerar_pdf_inaptos_graves()
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name="inaptos_graves.pdf")

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
    return render_template("pages/calouros.html", dados=dados)

# ── Configurações ──────────────────────────────────────────────────────────

@app.route("/config", methods=["GET", "POST"])
def configuracoes():
    global CONFIG
    from models import salvar_config_semestre
    if request.method == "POST":
        action = request.form.get("action", "amarelos")
        if action == "semestre":
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
        else:
            limite = request.form.get("limite_amarelos", "2")
            conn = get_conn()
            conn.execute(
                "UPDATE config SET valor=? WHERE chave='limite_amarelos'",
                (limite,)
            )
            conn.commit()
            conn.close()
            registrar_log("ALTERACAO_CONFIG", f"Limite de amarelos alterado para {limite}.")
        flash("Configurações salvas.", "success")
        return redirect(url_for("configuracoes"))
    limite_atual = get_config("limite_amarelos", "2")
    return render_template("pages/config.html", limite_amarelos=limite_atual, config_semestre=CONFIG)

# ── CRUD Padrinhos ─────────────────────────────────────────────────────────

@app.route("/padrinhos/<int:padrinho_id>/editar", methods=["POST"])
def editar_padrinho(padrinho_id):
    from models import editar_padrinho as _editar
    nome = request.form["nome"].strip()
    _editar(
        padrinho_id,
        nome,
        request.form["matricula"].strip(),
        request.form.get("email", "").strip(),
        request.form.get("telefone", "").strip(),
        request.form.get("turno", "").strip(),
    )
    registrar_log("EDICAO_PADRINHO", f"Padrinho '{nome}' (ID {padrinho_id}) atualizado.")
    flash("Padrinho atualizado.", "success")
    return redirect(url_for("padrinho_detalhe", padrinho_id=padrinho_id))

@app.route("/padrinhos/<int:padrinho_id>/excluir", methods=["POST"])
def excluir_padrinho(padrinho_id):
    from models import excluir_padrinho as _excluir
    p = get_padrinho(padrinho_id)
    _excluir(padrinho_id)
    registrar_log("EXCLUSAO_PADRINHO", f"Padrinho '{p['nome']}' (ID {padrinho_id}) removido do programa.")
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
    registrar_log("EXCLUSAO_ADVERTENCIA", f"Advertência ID {advertencia_id} removida (padrinho ID {padrinho_id}).")
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

@app.route("/reunioes/<int:reuniao_id>/editar", methods=["POST"])
def editar_reuniao(reuniao_id):
    from models import editar_reuniao as _editar
    _editar(
        reuniao_id,
        request.form["data"],
        request.form.get("tema", "").strip(),
        request.form.get("descricao", "").strip(),
    )
    registrar_log("EDICAO_REUNIAO", f"Reunião ID {reuniao_id} atualizada.")
    flash("Reunião atualizada.", "success")
    return redirect(url_for("reunioes"))

# ── CRUD Temas ─────────────────────────────────────────────────────────────

@app.route("/temas/<int:tema_id>/excluir", methods=["POST"])
def excluir_tema(tema_id):
    from models import excluir_tema as _excluir
    _excluir(tema_id)
    flash("Tema removido.", "success")
    return redirect(url_for("temas"))

@app.route("/temas/<int:tema_id>/editar", methods=["POST"])
def editar_tema(tema_id):
    from models import editar_tema as _editar
    _editar(
        tema_id,
        request.form["titulo"].strip(),
        request.form.get("data_aviso", ""),
        request.form["data_limite"],
        request.form.getlist("padrinho_ids"),
    )
    registrar_log("EDICAO_TEMA", f"Tema ID {tema_id} atualizado.")
    flash("Tema atualizado.", "success")
    return redirect(url_for("temas"))

# ── Match ─────────────────────────────────────────────────────────────────

@app.route("/match")
def match():
    dados = get_calouros_match_completo()
    conn = get_conn()
    total_matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    total_calouros = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    total_padrinhos = conn.execute("SELECT COUNT(*) FROM padrinhos WHERE ativo=1").fetchone()[0]
    conn.close()
    return render_template("pages/match.html",
        dados=dados,
        total_matches=total_matches,
        total_calouros=total_calouros,
        total_padrinhos=total_padrinhos,
    )

@app.route("/match/rodar", methods=["POST"])
def match_rodar():
    from models import rodar_match as _rodar
    conn = get_conn()
    total_calouros = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    total_padrinhos = conn.execute("SELECT COUNT(*) FROM padrinhos WHERE ativo=1").fetchone()[0]
    conn.close()
    max_calouros = math.ceil(total_calouros / max(total_padrinhos, 1))
    resultado = _rodar(max_calouros=max_calouros, score_minimo=0)
    conn = get_conn()
    conn.execute("DELETE FROM matches")
    for grupo in resultado["resultado"]:
        for item in grupo["calouros"]:
            conn.execute(
                "INSERT OR IGNORE INTO matches (padrinho_id, calouro_id) VALUES (?, ?)",
                (grupo["padrinho"]["id"], item["calouro"]["id"])
            )
    conn.commit()
    conn.close()
    total = sum(len(g["calouros"]) for g in resultado["resultado"])
    registrar_log("MATCH_GERADO", f"{total} matches gerados automaticamente.")
    flash(f"{total} matches gerados e confirmados.", "success")
    return redirect(url_for("match"))

@app.route("/match/resetar", methods=["POST"])
def match_resetar():
    conn = get_conn()
    conn.execute("DELETE FROM matches")
    conn.commit()
    conn.close()
    registrar_log("MATCH_RESETADO", "Todos os matches foram removidos.")
    flash("Matches resetados.", "success")
    return redirect(url_for("match"))

@app.route("/match/exportar")
def match_exportar():
    import csv, io
    from flask import Response
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.nome as padrinho_nome, p.turno, c.nome as calouro_nome, c.telefone
        FROM matches m
        JOIN padrinhos p ON p.id = m.padrinho_id
        JOIN calouros c ON c.id = m.calouro_id
        ORDER BY p.nome, c.nome
    """).fetchall()
    conn.close()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Padrinho", "Turno", "Calouro", "Telefone do Calouro"])
    for row in rows:
        writer.writerow([row["padrinho_nome"], row["turno"] or "—", row["calouro_nome"], row["telefone"] or "—"])
    return Response(
        buf.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=lista_contatos_match.csv"},
    )

# ── Logs de auditoria ─────────────────────────────────────────────────────

@app.route("/logs")
def logs():
    conn = get_conn()
    lista = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages/logs.html", logs=lista)

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

    return render_template("pages/importar_presencas.html", reuniao=reuniao)

# ── Relatórios HTML ───────────────────────────────────────────────────────

@app.route("/relatorio/aptidao")
def relatorio_aptidao():
    padrinhos = get_todos_padrinhos()
    limite = int(get_config("limite_amarelos", "2"))

    aprovados, reprovados, reportados = [], [], []
    conn = get_conn()

    for p in padrinhos:
        status_dict = calcular_status(p["id"], limite)
        status = status_dict["status"]
        historico = get_historico_padrinho(p["id"])
        presencas = sum(1 for pr in historico["presencas"] if pr["presente"])

        row = {
            "nome": p["nome"], "matricula": p["matricula"],
            "turno": p["turno"] or "—",
            "presencas": presencas,
            "num_amarelos": status_dict["amarelos"],
        }

        if status == "inapto_vermelho":
            adv = conn.execute(
                "SELECT motivo FROM advertencias WHERE padrinho_id=? AND tipo='vermelho' ORDER BY data DESC LIMIT 1",
                (p["id"],)
            ).fetchone()
            row["motivo_vermelho"] = adv["motivo"] if adv else "—"
            reportados.append(row)
        elif status == "inapto_amarelo":
            reprovados.append(row)
        else:
            aprovados.append(row)

    conn.close()

    return render_template("pages/relatorio_aptidao_acg.html",
        config=CONFIG,
        hoje=date.today(),
        total=len(padrinhos) or 1,
        aprovados=aprovados,
        reprovados=reprovados,
        reportados=reportados,
    )


@app.route("/relatorio/resumo")
def relatorio_resumo():
    padrinhos = get_todos_padrinhos()
    reunioes = get_todas_reunioes()
    temas_raw = get_todos_temas()
    limite = int(get_config("limite_amarelos", "2"))

    conn = get_conn()
    total_calouros = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    conn.close()

    contadores = {"aprovados": 0, "alerta": 0, "reprovados": 0, "reportados": 0}
    for p in padrinhos:
        status = calcular_status(p["id"], limite)["status"]
        if status == "apto":
            contadores["aprovados"] += 1
        elif status == "alerta":
            contadores["alerta"] += 1
        elif status == "inapto_amarelo":
            contadores["reprovados"] += 1
        elif status == "inapto_vermelho":
            contadores["reportados"] += 1

    temas = []
    for item in temas_raw:
        t = item["tema"]
        resp = ", ".join(p["nome"].split()[0] for p in item["padrinhos"]) or "—"
        data_limite = None
        if t["data_limite"]:
            try:
                data_limite = datetime.strptime(t["data_limite"], "%Y-%m-%d").date()
            except Exception:
                pass
        temas.append({
            "titulo": t["titulo"],
            "data_limite": data_limite,
            "responsaveis": resp,
            "situacao": t["situacao"] or "pendente",
        })

    from collections import Counter
    turno_counter = Counter(p["turno"] for p in padrinhos if p["turno"])
    total_com_turno = sum(turno_counter.values())
    turno_data = [
        {"turno": t, "qtd": q, "pct": round(q / total_com_turno * 100) if total_com_turno else 0}
        for t, q in sorted(turno_counter.items())
    ]

    return render_template("pages/relatorio_resumo_semestre.html",
        config=CONFIG,
        hoje=date.today(),
        total_padrinhos=len(padrinhos),
        total_calouros=total_calouros,
        total_reunioes=len(reunioes),
        temas=temas,
        n_aprovados=contadores["aprovados"],
        n_alerta=contadores["alerta"],
        n_reprovados=contadores["reprovados"],
        n_reportados=contadores["reportados"],
        limite_amarelos=limite,
        turno_data=turno_data,
    )


@app.route("/relatorio/reportados")
def relatorio_reportados():
    padrinhos = get_todos_padrinhos()
    limite = int(get_config("limite_amarelos", "2"))
    reportados = []

    conn = get_conn()
    for p in padrinhos:
        if calcular_status(p["id"], limite)["status"] == "inapto_vermelho":
            adv = conn.execute(
                "SELECT motivo, data FROM advertencias WHERE padrinho_id=? AND tipo='vermelho' ORDER BY data DESC LIMIT 1",
                (p["id"],)
            ).fetchone()
            data_adv = None
            if adv and adv["data"]:
                try:
                    data_adv = datetime.strptime(adv["data"], "%Y-%m-%d").date()
                except Exception:
                    pass
            reportados.append({
                "nome": p["nome"],
                "matricula": p["matricula"],
                "email": p["email"] or "—",
                "motivo_vermelho": adv["motivo"] if adv else "—",
                "data_advertencia_grave": data_adv,
            })
    conn.close()

    return render_template("pages/relatorio_reportados.html",
        config=CONFIG,
        hoje=date.today(),
        reportados=reportados,
    )


# ── Inicialização ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")