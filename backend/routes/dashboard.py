"""Dashboard: visão inicial com o status dos padrinhos e o resumo das reuniões."""

from flask import Blueprint, render_template

from backend.models import contar_reunioes, get_todos_padrinhos
from backend.repositories import reuniao_repository, tema_repository
from backend.services.status_service import calcular_todos_status

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
def dashboard():
    """Monta a visão inicial com status dos padrinhos e gráficos resumidos."""
    padrinhos = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    dados = [
        {"padrinho": p, **todos_status.get(p["id"], {"status": "apto", "amarelos": 0, "vermelhos": 0})}
        for p in padrinhos
    ]

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

    return render_template(
        "pages/dashboard.html",
        dados=dados,
        proxima_reuniao=proxima_reuniao,
        proximo_tema=proximo_tema,
        presencas_por_reuniao=presencas_por_reuniao,
    )
