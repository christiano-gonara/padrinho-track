"""Início do semestre: importação das planilhas e recarga dos dados de demonstração."""

import contextlib
import io

from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.database import get_conn
from backend.integrations.importers import (
    importar_calouros_sheets,
    importar_padrinhos_sheets,
)
from backend.models import get_config, registrar_log, set_config
from backend.repositories import match_repository, padrinho_repository

bp = Blueprint("inicio", __name__)

TABELAS_DO_PROGRAMA = (
    "matches",
    "calouros",
    "presencas",
    "advertencias",
    "tema_padrinhos",
    "temas",
    "reunioes",
    "padrinhos",
)


@bp.route("/inicio")
def inicio_semestre():
    """Tela operacional para importar dados no começo do semestre."""
    return render_template(
        "pages/inicio_semestre.html",
        total_padrinhos=padrinho_repository.contar_ativos(),
        total_calouros=match_repository.contar_calouros(),
        sheets_padrinhos_url=get_config("sheets_padrinhos_url", ""),
        sheets_calouros_url=get_config("sheets_calouros_url", ""),
    )


@bp.route("/inicio/importar-padrinhos", methods=["POST"])
def inicio_importar_padrinhos():
    """Importa padrinhos de uma planilha vinculada ao Google Forms."""
    url = request.form.get("sheets_padrinhos_url", "").strip()
    if url:
        set_config("sheets_padrinhos_url", url)
    else:
        url = get_config("sheets_padrinhos_url", "")
    if not url:
        flash("Cole o link da planilha antes de importar.", "error")
        return redirect(url_for("inicio.inicio_semestre"))
    try:
        resultado = importar_padrinhos_sheets(url)
        msg = (
            f"{resultado['importados']} padrinho(s) importado(s). "
            f"{resultado['ignorados']} ignorado(s) (curso diferente). "
            f"{resultado['duplicatas']} duplicata(s)."
        )
        registrar_log("IMPORTACAO_PADRINHOS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao importar: {e}", "error")
    return redirect(url_for("inicio.inicio_semestre"))


@bp.route("/inicio/importar-calouros", methods=["POST"])
def inicio_importar_calouros():
    """Importa calouros de uma planilha vinculada ao Google Forms."""
    url = request.form.get("sheets_calouros_url", "").strip()
    if url:
        set_config("sheets_calouros_url", url)
    else:
        url = get_config("sheets_calouros_url", "")
    if not url:
        flash("Cole o link da planilha antes de importar.", "error")
        return redirect(url_for("inicio.inicio_semestre"))
    try:
        resultado = importar_calouros_sheets(url)
        msg = (
            f"{resultado['importados']} calouro(s) importado(s). "
            f"{resultado['ignorados']} ignorado(s) (curso diferente). "
            f"{resultado['duplicatas']} duplicata(s)."
        )
        registrar_log("IMPORTACAO_CALOUROS", msg)
        flash(msg, "success")
    except Exception as e:
        flash(f"Erro ao importar: {e}", "error")
    return redirect(url_for("inicio.inicio_semestre"))


@bp.route("/seed-exemplo")
def seed_exemplo():
    """Recria o banco com dados fictícios de demonstração."""
    if request.args.get("senha") != "PucMinas2026":
        return "Acesso negado.", 403
    conn = get_conn()
    conn.execute(
        "TRUNCATE matches, calouros, presencas, advertencias,"
        " tema_padrinhos, temas, reunioes, padrinhos"
        " RESTART IDENTITY CASCADE"
    )
    conn.commit()
    conn.close()
    from scripts.seed_exemplo import seed

    seed()
    return redirect(url_for("dashboard.dashboard"))


@bp.route("/seed-real")
def seed_real():
    """Recria o banco local usando os scripts reais mantidos fora do Git."""
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
    for tabela in TABELAS_DO_PROGRAMA:
        conn.execute(f"DELETE FROM {tabela}")
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

    registrar_log(
        "SEED_REAL",
        "Seed real executado a partir de scripts/seed.py e scripts/seed_calouros.py.",
    )
    flash("Seed real executado com sucesso.", "success")
    return redirect(url_for("dashboard.dashboard"))
