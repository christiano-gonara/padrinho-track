"""Gera o site estático completo em docs/site para o GitHub Pages.

Copia o build React + TypeScript (web/dist) como aplicação principal interativa
(com cenários de uso e tema claro) e renderiza os exemplos reais de relatórios
e certificados A4 em docs/site/exemplos/ a partir de web/src/data/scenarios.json.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WEB_DIR = RAIZ / "web"
WEB_DIST = WEB_DIR / "dist"
WEB_STATIC = WEB_DIR / "static"
SCENARIOS_JSON = WEB_DIR / "src" / "data" / "scenarios.json"
SAIDA = RAIZ / "docs" / "site"
EXEMPLOS_DIR = SAIDA / "exemplos"

# O app exige estas variáveis para subir; o build estático não usa banco real.
os.environ.setdefault("SECRET_KEY", "build-do-site")
os.environ.setdefault("APP_PASSWORD", "build-do-site")

sys.path.insert(0, str(RAIZ))

from flask import render_template  # noqa: E402
from app import app  # noqa: E402


def _iso_to_date(texto):
    ano, mes, dia = (int(parte) for parte in texto.split("-"))
    return date(ano, mes, dia)


def _dados_exemplo():
    """Monta o contexto fictício dos exemplos A4 a partir do scenarios.json compartilhado."""
    bruto = json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))
    fechamento = bruto["scenarios"]["fechamento"]
    config = {**bruto["config"], "professor_coordenador_certificado": bruto["config"]["professor_coordenador"]}
    hoje = date(2026, 7, 20)

    padrinhos = bruto["padrinhosBase"]
    overrides = fechamento["statusOverrides"]

    aprovados = []
    reportados = []
    alerta_count = inapto_amarelo_count = 0

    for p in padrinhos:
        ov = overrides.get(str(p["id"]), {"status": "apto"})
        status = ov["status"]
        base_row = {
            "id": p["id"],
            "nome": p["nome"],
            "matricula": p["matricula"],
            "turno": p["turno"],
            "email": p["email"],
        }
        if status == "inapto_vermelho":
            adv = next((a for a in fechamento["advertencias"] if a["padrinho_id"] == p["id"] and a["tipo"] == "vermelho"), None)
            reportados.append({
                **base_row,
                "motivo_vermelho": adv["motivo"] if adv else "Ocorrência grave",
                "data_advertencia_grave": _iso_to_date(adv["data"]) if adv else hoje,
            })
        elif status == "inapto_amarelo":
            inapto_amarelo_count += 1
        else:
            aprovados.append(base_row)
            if status == "alerta":
                alerta_count += 1

    coordenacao = [
        {"indice": 0, "nome": config["coordenadora_geral"], "matricula": "—", "turno": "Coord.", "email": "—"},
        *(
            {"indice": idx, "nome": nome, "matricula": "—", "turno": "Coord.", "email": "—"}
            for idx, nome in enumerate(config["coordenadores"], start=1)
        ),
    ]
    paginas_aptidao = [
        {"tipo": "aprovados", "titulo": "Aptos para ACG", "linhas": aprovados, "inicio": 1},
        {"tipo": "reportados", "titulo": "Reportados ao Professor Coordenador", "linhas": reportados, "inicio": 1},
        {"tipo": "coordenacao", "titulo": "Coordenação para ACG", "linhas": coordenacao, "inicio": 1},
    ]

    total_padrinhos = len(padrinhos)
    total_calouros = len(bruto["calouros"])
    cal_manha = sum(1 for c in bruto["calouros"] if c["turno"] == "Manhã")
    cal_noite = total_calouros - cal_manha
    pad_manha = [p["nome"] for p in padrinhos if p["turno"] == "Manhã"]
    pad_noite = [p["nome"] for p in padrinhos if p["turno"] == "Noite"]

    ctx_aptidao = {
        "estatico": True,
        "config": config,
        "hoje": hoje,
        "total": total_padrinhos,
        "total_reunioes_db": len(fechamento["reunioes"]),
        "aprovados": aprovados,
        "reportados": reportados,
        "coordenacao": coordenacao,
        "paginas": paginas_aptidao,
        "total_paginas": len(paginas_aptidao),
        "has_turno": True,
    }

    ctx_resumo = {
        "estatico": True,
        "config": config,
        "hoje": hoje,
        "total_padrinhos": total_padrinhos,
        "total_calouros": total_calouros,
        "total_reunioes": len(fechamento["reunioes"]),
        "reunioes": [
            {"data": _iso_to_date(r["data"]), "tema": r["tema"], "descricao": r["descricao"]}
            for r in fechamento["reunioes"]
        ],
        "temas": [
            {
                "titulo": t["titulo"],
                "data_limite": _iso_to_date(t["data_limite"]),
                "responsaveis": ", ".join(r["nome"] for r in t["responsaveis"]),
                "qtd_responsaveis": len(t["responsaveis"]),
                "situacao": t["situacao"],
            }
            for t in fechamento["temas"]
        ],
        "padrinhos_por_turno": [
            {"turno": "Manhã", "qtd": len(pad_manha), "nomes": pad_manha},
            {"turno": "Noite", "qtd": len(pad_noite), "nomes": pad_noite},
        ],
        "total_aptos_acg": len(aprovados),
        "total_nao_aptos": total_padrinhos - len(aprovados),
        "taxa_aptidao": round(len(aprovados) / max(total_padrinhos, 1) * 100),
        "total_aprovados": len(aprovados) - alerta_count,
        "total_alerta": alerta_count,
        "total_reprovados": inapto_amarelo_count,
        "total_reportados": len(reportados),
        "turno_data": [
            {"turno": "Manhã", "qtd": len(pad_manha), "pct": round(len(pad_manha) / total_padrinhos * 100)},
            {"turno": "Noite", "qtd": len(pad_noite), "pct": round(len(pad_noite) / total_padrinhos * 100)},
        ],
        "turno_data_cal": [
            {"turno": "Manhã", "qtd": cal_manha, "pct": round(cal_manha / total_calouros * 100)},
            {"turno": "Noite", "qtd": cal_noite, "pct": round(cal_noite / total_calouros * 100)},
        ],
        "pct_bolsista": round(sum(p["bolsista"] for p in padrinhos) / total_padrinhos * 100),
        "pct_bh": round(sum(p["cidade_bh"] for p in padrinhos) / total_padrinhos * 100),
        "pct_trabalha": round(sum(p["trabalha"] for p in padrinhos) / total_padrinhos * 100),
        "pct_bolsista_cal": 35,
        "pct_bh_cal": 55,
        "pct_trabalha_cal": 30,
    }

    ctx_certificado = {
        "estatico": True,
        "padrinho": aprovados[0],
        "total_padrinhos": total_padrinhos,
        "total_calouros": total_calouros,
        "semestre": config["semestre"],
        "config": config,
        "hoje": hoje,
        "funcao_certificado": {"titulo": "Madrinha", "texto": "madrinha"},
        "horas_acg": 4,
    }

    return ctx_aptidao, ctx_resumo, ctx_certificado


def main() -> int:
    if not (WEB_DIST / "index.html").exists():
        subprocess.run(["npm", "run", "build", "--", "--mode", "pages"], cwd=str(WEB_DIR), check=True)

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    shutil.copytree(WEB_DIST, SAIDA)

    EXEMPLOS_DIR.mkdir(parents=True, exist_ok=True)
    ctx_aptidao, ctx_resumo, ctx_certificado = _dados_exemplo()

    with app.test_request_context("/"):
        aptidao_html = render_template("pages/relatorio_aptidao_acg.html", **ctx_aptidao)
        resumo_html = render_template("pages/relatorio_resumo_semestre.html", **ctx_resumo)
        certificado_html = render_template("pages/certificado.html", **ctx_certificado)

    (EXEMPLOS_DIR / "relatorio-aptidao.html").write_text(aptidao_html, encoding="utf-8")
    (EXEMPLOS_DIR / "resumo-semestre.html").write_text(resumo_html, encoding="utf-8")
    (EXEMPLOS_DIR / "certificado.html").write_text(certificado_html, encoding="utf-8")
    (SAIDA / ".nojekyll").touch()

    shutil.copytree(WEB_STATIC, SAIDA / "static", dirs_exist_ok=True)

    tamanho = sum(f.stat().st_size for f in SAIDA.rglob("*") if f.is_file())
    print(f"docs/site gerado: {len(list(SAIDA.rglob('*')))} arquivos, {tamanho / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
