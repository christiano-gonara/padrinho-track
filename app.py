import os
import sqlite3
from dotenv import load_dotenv
load_dotenv(override=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import date, datetime
from database import init_db, get_conn
import math
from models import (
    get_todos_padrinhos, get_padrinho, cadastrar_padrinho,
    get_todas_reunioes, criar_reuniao,
    lancar_presenca, get_presencas_reuniao, emitir_advertencias_falta,
    registrar_tema, registrar_entrega_tema, marcar_tema_nao_entregue,
    emitir_advertencia_manual, get_advertencias_padrinho,
    calcular_status, calcular_todos_status, get_historico_padrinho, get_relatorio_geral,
    get_todos_temas, get_calouros_match_completo, registrar_log,
    abreviar_nome, get_config_semestre, get_config, set_config, contar_reunioes,
    redistribuir_calouros, sincronizar_presencas_sheets,
    sincronizar_responsaveis_temas,
    importar_padrinhos_sheets, importar_calouros_sheets,
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

with app.app_context():
    init_db()

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
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    dados = [{"padrinho": p, **todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})} for p in padrinhos]

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
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in lista], limite)
    padrinhos_com_status = []
    for p in lista:
        d = dict(p)
        d["status"] = todos_status.get(p["id"], {"status": "apto"})["status"]
        padrinhos_com_status.append(d)
    return render_template("pages/padrinhos.html", padrinhos=padrinhos_com_status)

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
    sheets_url = get_config("sheets_presenca_url", "")
    return render_template("pages/reunioes.html", reunioes=lista, sheets_presenca_url=sheets_url)

@app.route("/reunioes/<int:reuniao_id>/sincronizar", methods=["POST"])
def reuniao_sincronizar(reuniao_id):
    try:
        resultado = sincronizar_presencas_sheets(reuniao_id)
        msg = f"{resultado['registradas']} presença(s) registrada(s)."
        if resultado["nao_reconhecidas"]:
            nomes = ", ".join(resultado["nao_reconhecidas"][:5])
            msg += f" {len(resultado['nao_reconhecidas'])} não reconhecida(s): {nomes}"
        registrar_log("SINCRONIZAR_PRESENCAS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao sincronizar: {e}", "error")
    return redirect(url_for("reunioes"))

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
    sheets_url = get_config("sheets_inscricoes_url", "")
    total_p = len(padrinhos)
    total_t = len(lista)
    if total_t > 0 and total_p > 0:
        base = total_p // total_t
        excedente = total_p % total_t
        sugestao_vagas = {"base": base, "excedente": excedente,
                          "total_padrinhos": total_p, "total_temas": total_t}
    else:
        sugestao_vagas = None
    ultimo_prazo = lista[-1]["tema"]["data_limite"] if lista else ""
    return render_template("pages/temas.html", temas=lista, padrinhos=padrinhos,
                           today=date.today().isoformat(), sheets_inscricoes_url=sheets_url,
                           sugestao_vagas=sugestao_vagas, ultimo_prazo=ultimo_prazo)

@app.route("/temas/configurar-inscricoes", methods=["POST"])
def temas_configurar_inscricoes():
    url = request.form.get("sheets_inscricoes_url", "").strip()
    set_config("sheets_inscricoes_url", url)
    registrar_log("ALTERACAO_CONFIG", "URL da planilha de inscrições em temas atualizada.")
    flash("Link salvo com sucesso.", "success")
    return redirect(url_for("temas"))

@app.route("/temas/sincronizar", methods=["POST"])
def temas_sincronizar():
    try:
        resultado = sincronizar_responsaveis_temas()
        msg = f"{resultado['atualizados']} responsável(eis) atualizado(s)."
        if resultado["nao_reconhecidos"]:
            nomes = ", ".join(resultado["nao_reconhecidos"][:5])
            msg += f" {len(resultado['nao_reconhecidos'])} não reconhecido(s): {nomes}"
        registrar_log("SINCRONIZAR_TEMAS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao sincronizar: {e}", "error")
    return redirect(url_for("temas"))

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
    total_reunioes = contar_reunioes()
    return render_template("pages/advertencias.html", advertencias=lista, padrinhos=padrinhos, total_reunioes=total_reunioes)

@app.route("/advertencias/manual", methods=["POST"])
def advertencia_manual():
    padrinho_id = request.form["padrinho_id"]
    motivo      = request.form["motivo"].strip()
    tipo        = request.form.get("tipo", "vermelho")
    if tipo not in ("amarelo", "vermelho"):
        tipo = "vermelho"
    emitir_advertencia_manual(padrinho_id, motivo, tipo)
    registrar_log("ADVERTENCIA_MANUAL", f"Advertência manual ({tipo}) para padrinho ID {padrinho_id}: {motivo}")
    flash("Advertência manual registrada.", "error")
    return redirect(url_for("advertencias"))

# ── Relatório ──────────────────────────────────────────────────────────────

@app.route("/relatorio")
def relatorio():
    dados = get_relatorio_geral()
    padrinhos_raw = get_todos_padrinhos()
    total = len(padrinhos_raw) or 1
    por_turno = {}
    n_fem = n_masc = n_bolsista = n_bh = n_trabalha = 0
    for p in padrinhos_raw:
        turno = p["turno"] or "—"
        por_turno[turno] = por_turno.get(turno, 0) + 1
        if p["genero"] == "F":
            n_fem += 1
        elif p["genero"] == "M":
            n_masc += 1
        if p["bolsista"]:
            n_bolsista += 1
        if p["cidade_bh"]:
            n_bh += 1
        if p["trabalha"]:
            n_trabalha += 1
    stats = {
        "por_turno": por_turno,
        "pct_feminino": round(n_fem / total * 100),
        "pct_masculino": round(n_masc / total * 100),
        "pct_bolsista": round(n_bolsista / total * 100),
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

# ── CRUD Padrinhos ─────────────────────────────────────────────────────────

@app.route("/padrinhos/<int:padrinho_id>/editar", methods=["POST"])
def editar_padrinho(padrinho_id):
    from models import editar_padrinho as _editar
    nome = request.form["nome"].strip()
    idade_s = request.form.get("idade", "").strip()
    passou_s = request.form.get("passou_algoritmos", "")
    _editar(
        padrinho_id,
        nome,
        request.form["matricula"].strip(),
        request.form.get("email", "").strip(),
        request.form.get("telefone", "").strip(),
        request.form.get("turno", "").strip(),
        genero=request.form.get("genero", "").strip() or None,
        idade=int(idade_s) if idade_s.isdigit() else None,
        cidade_bh=1 if request.form.get("cidade_bh") else 0,
        bolsista=1 if request.form.get("bolsista") else 0,
        trabalha=1 if request.form.get("trabalha") else 0,
        periodo=request.form.get("periodo", "").strip() or None,
        passou_algoritmos=int(passou_s) if passou_s in ("0", "1") else None,
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

@app.route("/match/lista-contatos")
def match_lista_contatos():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.nome as padrinho_nome, p.turno, c.nome as calouro_nome, c.telefone
        FROM matches m
        JOIN padrinhos p ON p.id = m.padrinho_id
        JOIN calouros c ON c.id = m.calouro_id
        ORDER BY p.nome, c.nome
    """).fetchall()
    conn.close()
    return render_template("pages/lista_contatos.html", rows=rows, config=CONFIG, hoje=date.today())

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

@app.route("/reunioes/configurar-forms", methods=["POST"])
def reunioes_configurar_forms():
    url = request.form.get("sheets_presenca_url", "").strip()
    set_config("sheets_presenca_url", url)
    registrar_log("ALTERACAO_CONFIG", "URL da planilha de presença atualizada.")
    flash("Link salvo com sucesso.", "success")
    return redirect(url_for("reunioes"))

# ── Backup do banco ───────────────────────────────────────────────────────

@app.route("/config/backup-db")
def backup_db():
    from flask import send_file
    from database import DB_PATH
    from datetime import date as _date
    nome = f"mentoria_{_date.today().isoformat()}.db"
    registrar_log("BACKUP_DB", "Backup do banco exportado pelo coordenador.")
    return send_file(str(DB_PATH), as_attachment=True, download_name=nome)

# ── Logs de auditoria ─────────────────────────────────────────────────────

@app.route("/logs/limpar", methods=["POST"])
def logs_limpar():
    conn = get_conn()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    registrar_log("LOGS_LIMPOS", "Logs de auditoria apagados pelo coordenador.")
    flash("Logs de auditoria apagados.", "success")
    return redirect(url_for("configuracoes"))

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
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)

    conn = get_conn()
    vermelho_rows = conn.execute(
        "SELECT padrinho_id, motivo, data FROM advertencias WHERE tipo='vermelho' ORDER BY data DESC"
    ).fetchall()
    conn.close()
    vermelho_map = {}
    for r in vermelho_rows:
        if r["padrinho_id"] not in vermelho_map:
            data_obj = None
            if r["data"]:
                try:
                    data_obj = datetime.strptime(r["data"], "%Y-%m-%d").date()
                except Exception:
                    pass
            vermelho_map[r["padrinho_id"]] = {"motivo": r["motivo"] or "—", "data": data_obj}

    aprovados, reportados = [], []
    for p in padrinhos:
        status_dict = todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})
        status = status_dict["status"]
        row = {
            "id": p["id"],
            "nome": p["nome"], "matricula": p["matricula"],
            "turno": p["turno"] or "—",
            "email": p["email"] or "—",
            "num_amarelos": status_dict["amarelos"],
        }
        if status == "inapto_vermelho":
            adv = vermelho_map.get(p["id"], {})
            row["motivo_vermelho"] = adv.get("motivo", "—")
            row["data_advertencia_grave"] = adv.get("data")
            reportados.append(row)
        elif status in ("apto", "alerta"):
            aprovados.append(row)

    return render_template("pages/relatorio_aptidao_acg.html",
        config=CONFIG,
        hoje=date.today(),
        total=len(padrinhos) or 1,
        total_reunioes_db=limite,
        aprovados=aprovados,
        reportados=reportados,
    )


@app.route("/relatorio/certificado/<int:padrinho_id>")
def relatorio_certificado(padrinho_id):
    p = get_padrinho(padrinho_id)
    if not p:
        return "Padrinho não encontrado.", 404
    limite = contar_reunioes()
    todos_status = calcular_todos_status([padrinho_id], limite)
    status = todos_status.get(padrinho_id, {"status": "apto"})["status"]
    if status not in ("apto", "alerta"):
        return "Este padrinho não está apto para receber certificado.", 403
    total_padrinhos = len(get_todos_padrinhos())
    conn = get_conn()
    total_calouros = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    conn.close()
    return render_template("pages/certificado.html",
        padrinho=p,
        total_padrinhos=total_padrinhos,
        total_calouros=total_calouros,
        semestre=CONFIG["semestre"],
        config=CONFIG,
        hoje=date.today(),
    )


@app.route("/relatorio/resumo")
def relatorio_resumo():
    padrinhos = get_todos_padrinhos()
    reunioes = get_todas_reunioes()
    temas_raw = get_todos_temas()

    conn = get_conn()
    cal_row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(bolsista) AS bol, SUM(cidade_bh) AS bh, SUM(trabalha) AS trab FROM calouros"
    ).fetchone()
    cal_turnos_raw = conn.execute(
        "SELECT turno, COUNT(*) AS qtd FROM calouros WHERE turno IS NOT NULL AND turno != '' GROUP BY turno ORDER BY turno"
    ).fetchall()
    conn.close()
    total_calouros = cal_row["total"] or 0
    total_cal_d = total_calouros or 1
    pct_bolsista_cal = round((cal_row["bol"] or 0) / total_cal_d * 100)
    pct_bh_cal       = round((cal_row["bh"]  or 0) / total_cal_d * 100)
    pct_trabalha_cal = round((cal_row["trab"] or 0) / total_cal_d * 100)
    total_turno_cal = sum(r["qtd"] for r in cal_turnos_raw)
    turno_data_cal = [
        {"turno": r["turno"], "qtd": r["qtd"], "pct": round(r["qtd"] / total_turno_cal * 100) if total_turno_cal else 0}
        for r in cal_turnos_raw
    ]

    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    contadores = {"aprovados": 0, "alerta": 0, "reprovados": 0, "reportados": 0}
    for p in padrinhos:
        status = todos_status.get(p["id"], {"status": "apto"})["status"]
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

    total_p = len(padrinhos) or 1
    pct_bolsista = round(sum(1 for p in padrinhos if p["bolsista"]) / total_p * 100)
    pct_bh       = round(sum(1 for p in padrinhos if p["cidade_bh"]) / total_p * 100)
    pct_trabalha = round(sum(1 for p in padrinhos if p["trabalha"]) / total_p * 100)

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
        turno_data=turno_data,
        turno_data_cal=turno_data_cal,
        pct_bolsista=pct_bolsista,
        pct_bh=pct_bh,
        pct_trabalha=pct_trabalha,
        pct_bolsista_cal=pct_bolsista_cal,
        pct_bh_cal=pct_bh_cal,
        pct_trabalha_cal=pct_trabalha_cal,
    )



# ── Início do Semestre ────────────────────────────────────────────────────

@app.route("/inicio")
def inicio_semestre():
    conn = get_conn()
    total_padrinhos = conn.execute("SELECT COUNT(*) FROM padrinhos WHERE ativo=1").fetchone()[0]
    total_calouros  = conn.execute("SELECT COUNT(*) FROM calouros").fetchone()[0]
    conn.close()
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
    if request.args.get("senha") != "PucMinas2026":
        return "Acesso negado.", 403
    from scripts.seed_exemplo import seed
    seed()
    return redirect(url_for("dashboard"))


@app.route("/seed-real")
def seed_real():
    if request.args.get("senha") != "PucMinas2026":
        return "Acesso negado.", 403

    _padrinhos = [
        ("Aléxia Andrade",                            "904175",   "afaandrade@sga.pucminas.br",               "31982716174",  "Noite"),
        ("Amanda Bicalho Silva",                       "1440377",  "amandabicalho.silva2004@gmail.com",        "31995748757",  "Noite"),
        ("Anny Victorya Azevedo Oliveira",             "899228",   "anny.azevedo@sga.pucminas.br",             "99984180594",  "Manhã"),
        ("Arthur Chaves Viana Leão",                   "890357",   "arthurcvleao@gmail.com",                   "31920086721",  "Noite"),
        ("Arthur Henrique Teixeira e Silva Bacelete",  "859123",   "abacelete@sga.pucminas.br",                "31992412598",  "Noite"),
        ("Caio Alves Kfuri",                           "882124",   "caio.kfuri@sga.pucminas.br",               "31998933914",  "Noite"),
        ("Charles Henrique de Paula Santos",           "901364",   "charles.santos@sga.pucminas.br",           "31971823055",  "Manhã"),
        ("Daniel Bony Costa Garcia",                   "891941",   "danielbony2105@gmail.com",                 "31980253599",  "Noite"),
        ("Diogo Augusto Magalhães Marques",            "902663",   "",                                         "31972266383",  "Noite"),
        ("Eli Júnior Domingos Dias",                   "892002",   "ejddias@sga.pucminas.br",                  "34997766769",  "Noite"),
        ("Fillipe Gabriel Costa Araujo",               "891942",   "",                                         "31972544985",  "Noite"),
        ("Gabriel Bruno da Cruz",                      "897952",   "",                                         "31999513818",  "Manhã"),
        ("Gabriel Chagas Lage",                        "803292",   "gabriel.lage.1197972@sga.pucminas.br",     "31980303049",  "Noite"),
        ("Gabriel Santos Martins",                     "885155",   "",                                         "31995289088",  "Manhã"),
        ("Giovana Lott Riquetti",                      "885433",   "",                                         "31987033048",  "Manhã"),
        ("Guilherme de Almeida Santos",                "800877",   "guilherme.santos.1439116@sga.pucminas.br", "31988442004",  "Noite"),
        ("Gustavo Azi Prehl Gama",                     "754737",   "gustavoprehl976@gmail.com",                "31971290021",  "Noite"),
        ("Gustavo Rodrigues Barbara Moreira",          "898623",   "grbmoreira@sga.pucminas.br",               "33999131666",  "Manhã"),
        ("Henrique Pereira Resende Rocha",             "893029",   "",                                         "31998608267",  "Manhã"),
        ("Igor Augusto Amaral Luz",                    "873059",   "igoraugusto.contato1@gmail.com",           "31998852227",  "Noite"),
        ("Italo Eduardo Carneiro da Silva",            "898961",   "italo.carneiro@sga.pucminas.br",           "31995387581",  "Noite"),
        ("João Paulo Gobira Lopes Costa",              "859611",   "joao.costa.1520911@sga.pucminas.br",       "33987632175",  "Noite"),
        ("João Pedro Lima de Andrade",                 "8853177",  "joao.andrade.1554805@sga.pucminas.br",     "31995112602",  "Manhã"),
        ("João Pedro Lisboa Augusto De Brito",         "878899",   "joao.augusto@sga.pucminas.br",             "31996690693",  "Noite"),
        ("João Pedro Moura Santos",                    "815677",   "joaopedros639@gmail.com",                  "31989206085",  "Noite"),
        ("João Vitor Tolentino",                       "838850",   "joaovitornll@gmail.com",                   "31985689938",  "Noite"),
        ("Joaquim Antonio Soares Camargos Souza",      "895700",   "joaquim.antonio.camargos@gmail.com",       "33998640504",  "Manhã"),
        ("Karen Joilly Araújo",                        "874309",   "karenjoilly@gmail.com",                    "31975684844",  "Manhã"),
        ("Laura Noronha Lara",                         "885231",   "",                                         "31975712192",  "Manhã"),
        ("Leonardo de Freitas Viana",                  "802807",   "",                                         "31984407033",  "Noite"),
        ("Lucas Batista Duarte",                       "880789",   "lucas.duarte.1548875@sga.pucminas.br",     "31982678631",  "Noite"),
        ("Lucas Moraes Rocha Spiazzi",                 "1594433",  "",                                         "31999104670",  "Manhã"),
        ("Luiz Felipe Ribeiro Souza",                  "888443",   "",                                         "31988890952",  "Manhã"),
        ("Mateus Marcal Ribas Marques",                "883531",   "mateus.marques.1583479@sga.pucminas.br",   "31994026879",  "Noite"),
        ("Matheus Barbosa",                            "889685",   "",                                         "31983954435",  "Noite"),
        ("Matheus Caetano Rocha",                      "838392",   "matheuscaetanorocha@gmail.com",            "31987746222",  "Noite"),
        ("Murilo Duarte Moura de Almeida",             "874486",   "",                                         "31993557359",  "Noite"),
        ("Pedro Henrique Pires Rodrigues",             "816373",   "",                                         "31984537619",  "Noite"),
        ("Pedro Rodrigues Duarte",                     "802915",   "artedudurty@gmail.com",                    "31975744647",  "Manhã"),
        ("Rafael Abras Lessa Freitas",                 "886358",   "rafaellessa2006@gmail.com",                "31985913087",  "Noite"),
        ("Rayssa Pierre da Silva Ramiro",              "828701",   "",                                         "31992674951",  "Noite"),
        ("Thomás Ramos Oliveira",                      "846130",   "thomas.oliveira@sga.pucminas.br",          "37999756056",  "Noite"),
        ("Vinícius Matos Oliveira Rocha",              "898073",   "vnmatoz33@gmail.com",                      "31981160375",  "Manhã"),
        ("Vitor de Roma Honório",                      "890180",   "",                                         "31975029406",  "Noite"),
        ("Vitor Veiga Silva",                          "857595",   "",                                         "31997388713",  "Noite"),
        ("João Felipe da Silva Prado",                 "856240",   "joaofprado13@gmail.com",                   "31973086408",  "Noite"),
    ]

    _matches = [
        ("Aléxia Andrade", [
            ("Maria Luiza Aparecida Trindade de Meneses", "31971650966"),
            ("Sophia de Fátima Simões Almeida", "31984618347"),
        ]),
        ("Amanda Bicalho Silva", [
            ("Ana ayla Pires Reis", "31971156263"),
            ("Luiza Morais Braga", "31998992307"),
        ]),
        ("Anny Victorya Azevedo Oliveira", [
            ("Larissa Fineli", "31997991668"),
            ("Fernando Pereira de Vasconcellos", "31999958706"),
            ("Estêvão de Castro Jung", "31993968896"),
            ("Giovana Faria Martins", "31985873475"),
            ("Priscilla Louzada Nesio", "31984543660"),
        ]),
        ("Arthur Chaves Viana Leão", [
            ("Lucca Marinho Eterovik Tavares Pereira", "31993840016"),
            ("Maria Fernanda Melo e Reis", "31986867777"),
        ]),
        ("Arthur Henrique Teixeira e Silva Bacelete", [
            ("Marcelo Esteves Bernardi", "31988577070"),
            ("Vítor Augusto de Souza", "31982266757"),
        ]),
        ("Caio Alves Kfuri", [
            ("Francisco Filipe da Cunha Oliveira", "31984548894"),
            ("Leonardo Federici Pettersen", "31986906362"),
        ]),
        ("Charles Henrique de Paula Santos", [
            ("João Victor Martins Pascoalon", "31987614784"),
            ("Pedro Henrique Soares Silva", "31984671221"),
            ("Tais Ribeiro Pereira Dias", "31973638071"),
            ("Vinicius Eduardo de Souza Matos Silva", "31995368328"),
        ]),
        ("Daniel Bony Costa Garcia", [
            ("Francisco de Castro Côrtes Netto", "31982853225"),
            ("Giovanna Marques Freire Barbosa", "31981179112"),
        ]),
        ("Diogo Augusto Magalhães Marques", [
            ("Lucas Gomes Esteves Da Silva", "31989277570"),
            ("Gabriel Mota Valério", "31986512527"),
        ]),
        ("Eli Júnior Domingos Dias", [
            ("Luís Gustavo Ribeiro Carvalho", "37998592749"),
            ("Gabriel de Oliveira Costa", "31988420928"),
            ("Arthur Moreira", "31993598577"),
        ]),
        ("Fillipe Gabriel Costa Araujo", [
            ("Gabriel Oliveira Gonzaga Araujo", "31998118684"),
            ("Gabriel Henrique de Souza Rodrigues", "31975616619"),
        ]),
        ("Gabriel Bruno da Cruz", [
            ("Lukas Nathan Matos Candeia", "31988378504"),
            ("Gabriel Cédric Carvalho Damazio", "31996814818"),
            ("Guilherme Ferreira Valadares", "33999657071"),
            ("Vinícius Marx Galvão", "31983768220"),
        ]),
        ("Gabriel Chagas Lage", [
            ("Paulo César Silva Monteiro", "31997046525"),
            ("Pedro Henrique Rocha", "31990702211"),
        ]),
        ("Gabriel Santos Martins", [
            ("Henrique de Freitas Issa", "31997756990"),
            ("Armando Schoenstatt Rodrigues e Moreira", "31971831645"),
            ("Henrique Victor de Figueiredo Coelho", "31994175572"),
            ("Giovanni Arenare Mota", "31996985853"),
        ]),
        ("Giovana Lott Riquetti", [
            ("Letícia Xavier Abreu", "31996559598"),
            ("Carolina Almeida Mendes de Souza", "73999667676"),
            ("Pedro Henrique Da Silva Fonseca", "31994181185"),
            ("Isaque de Jesus Marra", "31972342069"),
            ("Rafael Lima Pais", "31992528311"),
        ]),
        ("Guilherme de Almeida Santos", [
            ("Kaique Rodrigues do Vale", "31990797242"),
            ("Rafael Mota Azevedo", "31997009509"),
        ]),
        ("Gustavo Azi Prehl Gama", [
            ("Gabriel Vinícius Soares Doti", "31971333671"),
            ("Frederico Marcos de Paula Marques", "31975960380"),
            ("Victor Corradi", "37984128754"),
        ]),
        ("Gustavo Rodrigues Barbara Moreira", [
            ("Igor Pereira Apolinário", "31998558453"),
            ("Mateus Evaristo Melo", "31998053708"),
            ("Pedro Henrique Alves Ferreira", "31991577033"),
            ("Kemily Eduardo da Luz", "31985956350"),
        ]),
        ("Henrique Pereira Resende Rocha", [
            ("Lucas Abijaode Alvarenga", "31999770483"),
            ("Lucca Lourenço Theophilo", "31998709146"),
            ("João Pedro Silva Dantas", "37991705517"),
            ("Arthur Moraes Braga Araujo", "31998386531"),
        ]),
        ("Igor Augusto Amaral Luz", [
            ("Felipe Gabriel Nogueira Aquino", "31991633214"),
            ("Mateus Ribeiro Paixão", "31984256316"),
        ]),
        ("Italo Eduardo Carneiro da Silva", [
            ("Daniel Gomes Rolando", "31985395309"),
            ("Crystian Marcondes Oliveira Nascimento", "31991425827"),
        ]),
        ("João Paulo Gobira Lopes Costa", [
            ("Igor Bruno Rodrigues da Cruz", "31997050133"),
            ("Filipe Mota Coelho", "38984057711"),
        ]),
        ("João Pedro Lima de Andrade", [
            ("Crispim Bruno Da Silva Junior", "32999842588"),
            ("Patrick Augusto de Oliveira", "32984917743"),
            ("Guilherme Miranda Presot", "31995406158"),
            ("Victor Reis Silva de Paula", "31997777135"),
            ("Pietro Reis Lopes Melo", "31996751315"),
        ]),
        ("João Pedro Lisboa Augusto De Brito", [
            ("Leonardo Martins Macedo", "31987451563"),
            ("Sophia Nicole Ferreira Reis Gonçalves", "31996200585"),
        ]),
        ("João Pedro Moura Santos", [
            ("Rafael Ferreira Torres Modesto", "31989790048"),
            ("Guilherme Luiz Santos Chebile", "31994683419"),
        ]),
        ("João Vitor Tolentino", [
            ("Guilherme Enzo Almeida Ferreira", "31999640753"),
            ("Rodrigo Ventura Teixeira", "31999921261"),
        ]),
        ("Joaquim Antonio Soares Camargos Souza", [
            ("Nathan Junquer de Almeida Castro", "31993638194"),
            ("Luis Fernando de Sousa Dias", "37999295615"),
            ("Beatriz Almeida", "31999270708"),
            ("Fernando Gomes Reis de Resende", "32998416568"),
        ]),
        ("Karen Joilly Araújo", [
            ("Maria Luiza Queiroz Martins da Silva", "31971866380"),
            ("Erick Calixto David Silva", "37999340513"),
            ("Pedro Henrique Silva Oliveira", "31992095958"),
            ("Samuel Ferreira Guimarães", "38999380823"),
        ]),
        ("Laura Noronha Lara", [
            ("Maria Clara Soalheiro Bessa", "33987161752"),
            ("Matheus Possemato Lopes", "31996190072"),
            ("Thiago Guerra de Araujo", "31995788144"),
            ("Larissa Cravo Carvalho Câmara Santos", "31982320889"),
        ]),
        ("Leonardo de Freitas Viana", [
            ("Lucas Dutra Figueiredo", "31984822660"),
            ("João Paulo de Castro", "31982707359"),
        ]),
        ("Lucas Batista Duarte", [
            ("Emanuel Phillipe Ribeiro Ferreira de Carvalho", "31982205685"),
            ("Lucas Franco Baia", "31996441678"),
            ("Victor Dante Fonseca Oliveira", "31723341700"),
        ]),
        ("Lucas Moraes Rocha Spiazzi", [
            ("Gabriel de Souza Junqueira Hermont", "31992021581"),
            ("Jorge Lucas Vieira", "31999769734"),
            ("Marcos Henrique Santos Lacerda", "37999346661"),
            ("Daniell Oliveira Cardoso de Sá", "31998007228"),
        ]),
        ("Luiz Felipe Ribeiro Souza", [
            ("Fernando De Oliveira Palheiros", "31989542063"),
            ("Abner Cordeiro de Almeida", "37998601606"),
            ("Davi Martins Alves", "33933006617"),
            ("Enzo Fernandes Alcântara", "31995612833"),
        ]),
        ("Mateus Marcal Ribas Marques", [
            ("Patrick da Lomba Fernandes de Souza", "31985220688"),
            ("Gabriel Sousa Aguiar", "31998231403"),
        ]),
        ("Matheus Barbosa", [
            ("Victhor Gabriel Freire de Oliveira", "38998668922"),
            ("Nicolas De Almeida", "33999100110"),
        ]),
        ("Matheus Caetano Rocha", [
            ("Isaque Eduardo Gonçalves de Paiva", "31993822133"),
            ("Vitor Ladeia Sepulveda", "31992855442"),
        ]),
        ("Murilo Duarte Moura de Almeida", [
            ("Yudy Samuell Magalhães Ramos", "31995762905"),
            ("Bernardo Guedes da Silveira", "31997161366"),
        ]),
        ("Pedro Henrique Pires Rodrigues", [
            ("Leonardo de Freitas Ávila", "31993290606"),
            ("Theo Goulart Cardoso Vasconcelos", "31984383189"),
        ]),
        ("Pedro Rodrigues Duarte", [
            ("Bernardo Arruda Leite", "37999261209"),
            ("Gabriel do Carmo Assis", "31988874742"),
            ("Mayra Luíza Santos da Silva", "38988667147"),
            ("Lucas Dias Melo", "37999477715"),
        ]),
        ("Rafael Abras Lessa Freitas", [
            ("Daniel Costa Alves da Cunha", "31986963894"),
            ("Pedro Henrique Nascimento Cezar", "31993951910"),
        ]),
        ("Rayssa Pierre da Silva Ramiro", [
            ("Núbia Torres de Oliveira", "31982515007"),
            ("Gabriela Pinheiro Pierazolli", "31971431230"),
        ]),
        ("Thomás Ramos Oliveira", [
            ("Gabriel Luiz Drumond Oliveira", "31993531529"),
            ("Maria Fernanda Ferreira Rangel", "31973164969"),
        ]),
        ("Vinícius Matos Oliveira Rocha", [
            ("Kaio Vinicius Souza Santos", "31997270759"),
            ("David Aurélio Pedrosa", "31983273314"),
            ("José Uliana", "31999646327"),
            ("Saul de Castro Macedo", "31982720660"),
            ("Paulo Henrique Pereira de Souza", "31999865670"),
        ]),
        ("Vitor de Roma Honório", [
            ("Hector Paulo Nogueira Xavier", "31987241720"),
            ("Italo Alves Machado", "31975460413"),
        ]),
        ("Vitor Veiga Silva", [
            ("Gabriel Rodrigues Lima", "31991760528"),
            ("Samuel Ricardo Rodrigues Silva", "31973653483"),
        ]),
    ]

    _temas = [
        ("Boas vindas e Setup",            "2026-03-23", "2026-03-27", ["Amanda Bicalho", "Pedro Rodrigues Duarte", "Igor Augusto"]),
        ("Lógica digital",                 "2026-03-27", "2026-04-06", ["Guilherme de Almeida", "João Vitor Tolentino", "Charles Henrique"]),
        ("Python 1: Entradas e saídas",    "2026-04-06", "2026-04-09", ["Gabriel Chagas", "Daniel Bony", "Fillipe Gabriel"]),
        ("Python 2: Condicionais",         "2026-04-10", "2026-04-16", ["Henrique Pereira", "Diogo Augusto", "Pedro Henrique Pires"]),
        ("Base numérica: conversão",       "2026-04-17", "2026-04-23", ["Gustavo Rodrigues Barbara", "Anny Victorya", "Matheus Barbosa"]),
        ("Base numérica: soma e subtração","2026-04-24", "2026-04-30", ["Arthur Henrique Teixeira", "João Paulo Gobira", "João Pedro Lisboa"]),
        ("Python 3: Laço while",           "2026-05-04", "2026-05-07", ["Joaquim Antonio", "Luiz Felipe Ribeiro", "Laura Noronha"]),
        ("Python 3: Laço for",             "2026-05-08", "2026-05-14", ["Gabriel Santos Martins", "João Pedro Lima de Andrade", "Gabriel Bruno"]),
        ("Python 5: funções",              "2026-05-15", "2026-05-21", ["Vitor Veiga", "Thomás Ramos", "Gustavo Azi Prehl"]),
        ("JavaScript Básico",              "2026-05-22", "2026-05-28", ["Aléxia Andrade", "João Pedro Moura", "Leonardo de Freitas"]),
        ("Git e boas práticas",            "2026-05-29", "2026-06-04", ["Lucas Batista", "Rafael Abras", "Italo Eduardo"]),
        ("HTML semântico e CSS Flexbox",   "2026-06-05", "2026-06-11", ["Mateus Marcal", "Caio Alves Kfuri", "Karen Joilly"]),
        ("Dom e Eventos",                  "2026-06-12", "2026-06-18", ["João Pedro Lisboa", "Arthur Chaves", "Eli Júnior"]),
        ("Carreira e LinkedIn",            "2026-06-19", "2026-06-25", ["Vitor de Roma", "Murilo Duarte"]),
        ("Como funcionam as horas de ACG", "2026-06-26", "2026-07-02", ["Giovana Lott", "Rayssa Pierre", "Lucas Moraes Rocha"]),
    ]

    conn1 = get_conn()
    conn1.execute(
        "TRUNCATE matches, calouros, presencas, advertencias,"
        " tema_padrinhos, temas, reunioes, padrinhos"
        " RESTART IDENTITY CASCADE"
    )
    conn1.commit()
    conn1.close()

    conn = get_conn()

    for nome, matricula, email, telefone, turno in _padrinhos:
        conn.execute(
            "INSERT INTO padrinhos (nome, matricula, email, telefone, turno) VALUES (?, ?, ?, ?, ?)",
            (nome, matricula, email, telefone, turno),
        )

    for titulo, data_aviso, data_limite, nomes in _temas:
        cur = conn.execute(
            "INSERT INTO temas (titulo, data_aviso, data_limite) VALUES (?, ?, ?)",
            (titulo, data_aviso, data_limite),
        )
        tema_id = cur.lastrowid
        for nome_parcial in nomes:
            row = conn.execute(
                "SELECT id FROM padrinhos WHERE nome LIKE ?", (f"%{nome_parcial}%",)
            ).fetchone()
            if row:
                conn.execute(
                    "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?, ?)",
                    (tema_id, row["id"]),
                )

    for nome_padrinho, calouros in _matches:
        padrinho = conn.execute(
            "SELECT id FROM padrinhos WHERE nome LIKE ?",
            (f"%{nome_padrinho.split()[0]}%{nome_padrinho.split()[-1]}%",),
        ).fetchone()
        if not padrinho:
            continue
        for nome_calouro, telefone in calouros:
            cur = conn.execute(
                "INSERT INTO calouros (nome, telefone) VALUES (?, ?)",
                (nome_calouro, telefone),
            )
            conn.execute(
                "INSERT INTO matches (padrinho_id, calouro_id) VALUES (?, ?)",
                (padrinho["id"], cur.lastrowid),
            )

    cur1 = conn.execute(
        "INSERT INTO reunioes (data, tema, descricao) VALUES (?, ?, ?)",
        ("2026-03-15", "Apresentação do Programa", "Reunião inaugural"),
    )
    reuniao1_id = cur1.lastrowid
    cur2 = conn.execute(
        "INSERT INTO reunioes (data, tema, descricao) VALUES (?, ?, ?)",
        ("2026-06-20", "Encerramento e ACG", "Reunião de encerramento"),
    )
    reuniao2_id = cur2.lastrowid

    for p in conn.execute("SELECT id FROM padrinhos WHERE ativo = 1").fetchall():
        for rid in (reuniao1_id, reuniao2_id):
            conn.execute(
                """INSERT INTO presencas (reuniao_id, padrinho_id, presente, justificada)
                   VALUES (?, ?, 1, 0)
                   ON CONFLICT(reuniao_id, padrinho_id)
                   DO UPDATE SET presente = 1, justificada = 0""",
                (rid, p["id"]),
            )

    conn.execute(
        "UPDATE temas SET situacao = 'entregue', data_entrega = ?",
        (date.today().isoformat(),),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

@app.route("/debug-status")
def debug_status():
    from models import get_todos_padrinhos, calcular_status, contar_reunioes
    from flask import jsonify
    padrinhos = get_todos_padrinhos()
    total_reunioes = contar_reunioes()
    resultados = []
    for p in padrinhos[:5]:
        s = calcular_status(p["id"])
        resultados.append({
            "nome": p["nome"],
            "status": s["status"],
            "amarelos": s["amarelos"],
            "vermelhos": s["vermelhos"],
        })
    return jsonify({
        "total_padrinhos": len(padrinhos),
        "total_reunioes": total_reunioes,
        "amostra": resultados,
    })


# ── Inicialização ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")