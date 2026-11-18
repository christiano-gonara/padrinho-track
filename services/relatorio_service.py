from collections import Counter
from datetime import date, datetime

from models import (
    contar_reunioes,
    get_relatorio_geral,
    get_todas_reunioes,
    get_todos_padrinhos,
    get_todos_temas,
)
from repositories import advertencia_repository, calouro_repository
from services.certificado_service import listar_coordenacao_certificados
from services.status_service import calcular_todos_status


def montar_contexto_relatorio_geral():
    """Monta dados da página principal de relatório dentro do sistema."""
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
    return {"dados": dados, "stats": stats}


def montar_contexto_aptidao_acg(config):
    """Monta aprovados/reportados para o relatório de aptidão ACG."""
    padrinhos = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)

    vermelho_rows = advertencia_repository.listar_vermelhas_recentes()

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
            "nome": p["nome"],
            "matricula": p["matricula"],
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

    paginas = []
    primeira_qtd = 15
    continuacao_qtd = 24
    if aprovados:
        paginas.append({
            "tipo": "aprovados",
            "titulo": "Aptos para ACG",
            "linhas": aprovados[:primeira_qtd],
            "inicio": 1,
        })
        for i in range(primeira_qtd, len(aprovados), continuacao_qtd):
            paginas.append({
                "tipo": "aprovados",
                "titulo": "Aptos para ACG",
                "linhas": aprovados[i:i + continuacao_qtd],
                "inicio": i + 1,
            })

    for i in range(0, len(reportados), 18):
        paginas.append({
            "tipo": "reportados",
            "titulo": "Reportados ao Professor Coordenador",
            "linhas": reportados[i:i + 18],
            "inicio": i + 1,
        })

    coordenacao = [
        {
            "indice": idx,
            "nome": pessoa["nome"],
            "matricula": "—",
            "turno": "Coord.",
            "email": "—",
        }
        for idx, pessoa in enumerate(listar_coordenacao_certificados(config))
    ]
    if coordenacao:
        paginas.append({
            "tipo": "coordenacao",
            "titulo": "Coordenação para ACG",
            "linhas": coordenacao,
            "inicio": 1,
        })

    if not paginas:
        paginas.append({"tipo": "aprovados", "titulo": "Aptos para ACG", "linhas": [], "inicio": 1})

    return {
        "config": config,
        "hoje": date.today(),
        "total": len(padrinhos) or 1,
        "total_reunioes_db": limite,
        "aprovados": aprovados,
        "reportados": reportados,
        "coordenacao": coordenacao,
        "paginas": paginas,
        "total_paginas": len(paginas),
        "has_turno": any(p["turno"] != "—" for p in aprovados),
    }


def montar_contexto_resumo_semestre(config):
    """Monta indicadores, reuniões, temas e participantes do resumo final."""
    padrinhos = get_todos_padrinhos()
    reunioes = get_todas_reunioes()
    temas_raw = get_todos_temas()

    cal_row = calouro_repository.obter_resumo_demografico()
    cal_turnos_raw = calouro_repository.contar_por_turno()

    total_calouros = cal_row["total"] or 0
    total_cal_d = total_calouros or 1
    pct_bolsista_cal = round((cal_row["bol"] or 0) / total_cal_d * 100)
    pct_bh_cal = round((cal_row["bh"] or 0) / total_cal_d * 100)
    pct_trabalha_cal = round((cal_row["trab"] or 0) / total_cal_d * 100)
    total_turno_cal = sum(r["qtd"] for r in cal_turnos_raw)
    turno_data_cal = [
        {
            "turno": r["turno"],
            "qtd": r["qtd"],
            "pct": round(r["qtd"] / total_turno_cal * 100) if total_turno_cal else 0,
        }
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
        prepos = {"de", "da", "do", "dos", "das"}
        resp = ", ".join(
            " ".join([pts[0]] + [parte for parte in pts[1:] if parte.lower() not in prepos][:1])
            for p in item["padrinhos"]
            for pts in [p["nome"].split()]
        ) or "—"
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
            "qtd_responsaveis": len(item["padrinhos"]),
            "situacao": t["situacao"] or "pendente",
        })

    reunioes_resumo = []
    for r in sorted(reunioes, key=lambda item: item["data"] or ""):
        data_reuniao = None
        if r["data"]:
            try:
                data_reuniao = datetime.strptime(r["data"], "%Y-%m-%d").date()
            except Exception:
                pass
        reunioes_resumo.append({
            "data": data_reuniao,
            "tema": r["tema"] or "Reunião",
            "descricao": r["descricao"] or "",
        })

    turno_counter = Counter(p["turno"] for p in padrinhos if p["turno"])
    total_com_turno = sum(turno_counter.values())
    turno_data = [
        {"turno": t, "qtd": q, "pct": round(q / total_com_turno * 100) if total_com_turno else 0}
        for t, q in sorted(turno_counter.items())
    ]
    padrinhos_por_turno = []
    for turno, nomes in sorted(
        {
            (p["turno"] or "Sem turno"): sorted([x["nome"] for x in padrinhos if (x["turno"] or "Sem turno") == (p["turno"] or "Sem turno")])
            for p in padrinhos
        }.items()
    ):
        padrinhos_por_turno.append({"turno": turno, "nomes": nomes, "qtd": len(nomes)})

    total_p = len(padrinhos) or 1
    total_aptos_acg = contadores["aprovados"] + contadores["alerta"]
    total_nao_aptos = contadores["reprovados"] + contadores["reportados"]

    return {
        "config": config,
        "hoje": date.today(),
        "total_padrinhos": len(padrinhos),
        "total_calouros": total_calouros,
        "total_reunioes": len(reunioes),
        "reunioes": reunioes_resumo,
        "temas": temas,
        "padrinhos_lista": sorted([p["nome"] for p in padrinhos]),
        "padrinhos_por_turno": padrinhos_por_turno,
        "total_aptos_acg": total_aptos_acg,
        "total_nao_aptos": total_nao_aptos,
        "taxa_aptidao": round(total_aptos_acg / total_p * 100),
        "total_aprovados": contadores["aprovados"],
        "total_alerta": contadores["alerta"],
        "total_reprovados": contadores["reprovados"],
        "total_reportados": contadores["reportados"],
        "turno_data": turno_data,
        "turno_data_cal": turno_data_cal,
        "pct_bolsista": round(sum(1 for p in padrinhos if p["bolsista"]) / total_p * 100),
        "pct_bh": round(sum(1 for p in padrinhos if p["cidade_bh"]) / total_p * 100),
        "pct_trabalha": round(sum(1 for p in padrinhos if p["trabalha"]) / total_p * 100),
        "pct_bolsista_cal": pct_bolsista_cal,
        "pct_bh_cal": pct_bh_cal,
        "pct_trabalha_cal": pct_trabalha_cal,
    }
