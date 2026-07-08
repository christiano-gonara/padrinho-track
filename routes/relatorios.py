from flask import Blueprint, render_template, request, send_file

from models import (
    get_config_semestre,
)
from services.certificado_service import (
    montar_contexto_certificado,
    montar_contexto_certificado_coordenacao,
    obter_zip_certificados,
)
from services.relatorio_service import (
    montar_contexto_aptidao_acg,
    montar_contexto_relatorio_geral,
    montar_contexto_resumo_semestre,
)


bp = Blueprint("relatorios", __name__)


@bp.route("/relatorio")
def relatorio():
    """Tela web com visão geral dos relatórios."""
    return render_template("pages/relatorio.html", **montar_contexto_relatorio_geral())


@bp.route("/relatorio/aptidao")
def relatorio_aptidao():
    """Renderiza o relatório HTML imprimível de aptidão ACG."""
    config = get_config_semestre()
    return render_template("pages/relatorio_aptidao_acg.html", **montar_contexto_aptidao_acg(config))


@bp.route("/relatorio/certificado/<int:padrinho_id>")
def relatorio_certificado(padrinho_id):
    """Renderiza o certificado individual de um padrinho apto."""
    config = get_config_semestre()
    contexto, erro, status = montar_contexto_certificado(padrinho_id, config)
    if erro:
        return erro, status
    return render_template("pages/certificado.html", **contexto)


@bp.route("/relatorio/certificado/coordenacao/<int:indice>")
def relatorio_certificado_coordenacao(indice):
    """Renderiza o certificado individual de uma pessoa da coordenação."""
    config = get_config_semestre()
    contexto, erro, status = montar_contexto_certificado_coordenacao(indice, config)
    if erro:
        return erro, status
    return render_template("pages/certificado.html", **contexto)


@bp.route("/relatorio/certificados/zip")
def relatorio_certificados_zip():
    """Baixa o ZIP com certificados individuais em PDF."""
    config = get_config_semestre()
    try:
        cache_path, download_name = obter_zip_certificados(
            config,
            regenerar=request.args.get("regenerar") == "1",
        )
    except RuntimeError as exc:
        return str(exc), 500

    return send_file(
        cache_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )


@bp.route("/relatorio/resumo")
def relatorio_resumo():
    """Renderiza o resumo final do semestre."""
    config = get_config_semestre()
    return render_template("pages/relatorio_resumo_semestre.html", **montar_contexto_resumo_semestre(config))
