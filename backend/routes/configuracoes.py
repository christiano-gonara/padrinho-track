"""Configurações do semestre, backup do banco e logs de auditoria."""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from backend.database import DB_PATH, get_conn
from backend.models import contar_reunioes, get_config_semestre, registrar_log, salvar_config_semestre

bp = Blueprint("configuracoes", __name__)


@bp.route("/config", methods=["GET", "POST"])
def configuracoes():
    """Exibe e salva as configurações gerais do semestre."""
    if request.method == "POST":
        coordenadores_raw = request.form.get("coordenadores", "")
        coordenadores = [n.strip() for n in coordenadores_raw.splitlines() if n.strip()]
        config = {
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
        salvar_config_semestre(config)
        registrar_log(
            "ALTERACAO_CONFIG",
            f"Configurações do semestre {config['semestre']} atualizadas.",
        )
        flash("Configurações salvas.", "success")
        return redirect(url_for("configuracoes.configuracoes"))

    return render_template(
        "pages/config.html",
        config_semestre=get_config_semestre(),
        total_reunioes=contar_reunioes(),
    )


@bp.route("/config/backup-db")
def backup_db():
    """Baixa uma cópia do banco SQLite local."""
    nome = f"mentoria_{date.today().isoformat()}.db"
    registrar_log("BACKUP_DB", "Backup do banco exportado pelo coordenador.")
    return send_file(str(DB_PATH), as_attachment=True, download_name=nome)


@bp.route("/logs")
def logs():
    """Mostra os logs de auditoria em ordem recente."""
    conn = get_conn()
    lista = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("pages/logs.html", logs=lista)


@bp.route("/logs/limpar", methods=["POST"])
def logs_limpar():
    """Limpa os logs de auditoria do sistema."""
    conn = get_conn()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    registrar_log("LOGS_LIMPOS", "Logs de auditoria apagados pelo coordenador.")
    flash("Logs de auditoria apagados.", "success")
    return redirect(url_for("configuracoes.configuracoes"))
