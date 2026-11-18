"""Gera o site estático completo em docs/site para o GitHub Pages.

Copia o build React + TypeScript (web/dist) como aplicação principal interativa
(com cenários de uso e tema claro) e renderiza os exemplos reais de relatórios
e certificados A4 em docs/site/exemplos/ a partir dos templates do sistema.
"""

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
SAIDA = RAIZ / "docs" / "site"
EXEMPLOS_DIR = SAIDA / "exemplos"

# O app exige estas variáveis para subir; o build estático não usa banco real.
os.environ.setdefault("SECRET_KEY", "build-do-site")
os.environ.setdefault("APP_PASSWORD", "build-do-site")

sys.path.insert(0, str(RAIZ))

from flask import render_template  # noqa: E402
from app import app  # noqa: E402


def _dados_exemplo():
    """Retorna contexto fictício consistente para os exemplos públicos no Pages."""
    config = {
        "semestre": "2026/1",
        "professor_coordenador": "Prof. Laerte Xavier",
        "professor_coordenador_certificado": "Prof. Laerte Xavier",
        "programa": "Mentoria Acadêmica — Engenharia de Software",
        "instituicao": "PUC Minas",
        "total_reunioes": 3,
        "coordenadora_geral": "Clara Vasconcelos",
        "coordenadores": ["Lucas Almeida", "Mariana Freitas"],
    }
    hoje = date(2026, 7, 20)

    aprovados = [
        {"id": 1, "nome": "Alice Mendonça", "matricula": "100001", "turno": "Manhã", "email": "alice.mendonca@exemplo.edu.br"},
        {"id": 2, "nome": "Bruno Tavares", "matricula": "100002", "turno": "Noite", "email": "bruno.tavares@exemplo.edu.br"},
        {"id": 3, "nome": "Camila Rezende", "matricula": "100003", "turno": "Manhã", "email": "camila.rezende@exemplo.edu.br"},
        {"id": 4, "nome": "Diego Fonseca", "matricula": "100004", "turno": "Noite", "email": "diego.fonseca@exemplo.edu.br"},
        {"id": 5, "nome": "Elisa Drummond", "matricula": "100005", "turno": "Manhã", "email": "elisa.drummond@exemplo.edu.br"},
        {"id": 6, "nome": "Felipe Quaresma", "matricula": "100006", "turno": "Noite", "email": "felipe.quaresma@exemplo.edu.br"},
        {"id": 7, "nome": "Gabriela Monteiro", "matricula": "100007", "turno": "Manhã", "email": "gabriela.monteiro@exemplo.edu.br"},
        {"id": 8, "nome": "Henrique Lacerda", "matricula": "100008", "turno": "Noite", "email": "henrique.lacerda@exemplo.edu.br"},
    ]
    reportados = [
        {
            "id": 10,
            "nome": "João Vasconcelos",
            "matricula": "100010",
            "turno": "Noite",
            "email": "joao.vasconcelos@exemplo.edu.br",
            "motivo_vermelho": "Não entrega do tema atribuído após prazo estendido",
            "data_advertencia_grave": date(2026, 5, 18),
        }
    ]
    coordenacao = [
        {"indice": 0, "nome": "Clara Vasconcelos", "matricula": "—", "turno": "Coord.", "email": "—"},
        {"indice": 1, "nome": "Lucas Almeida", "matricula": "—", "turno": "Coord.", "email": "—"},
        {"indice": 2, "nome": "Mariana Freitas", "matricula": "—", "turno": "Coord.", "email": "—"},
    ]
    paginas_aptidao = [
        {"tipo": "aprovados", "titulo": "Aptos para ACG", "linhas": aprovados, "inicio": 1},
        {"tipo": "reportados", "titulo": "Reportados ao Professor Coordenador", "linhas": reportados, "inicio": 1},
        {"tipo": "coordenacao", "titulo": "Coordenação para ACG", "linhas": coordenacao, "inicio": 1},
    ]

    ctx_aptidao = {
        "estatico": True,
        "config": config,
        "hoje": hoje,
        "total": 10,
        "total_reunioes_db": 3,
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
        "total_padrinhos": 10,
        "total_calouros": 20,
        "total_reunioes": 3,
        "reunioes": [
            {"data": date(2026, 3, 20), "tema": "Abertura do semestre", "descricao": "Apresentação das regras do programa e acolhimento inicial."},
            {"data": date(2026, 4, 17), "tema": "Acompanhamento de temas", "descricao": "Alinhamento de dúvidas dos calouros e cronograma de atividades."},
            {"data": date(2026, 6, 12), "tema": "Fechamento e balanço", "descricao": "Revisão de entregas e feedback do semestre."},
        ],
        "temas": [
            {"titulo": "Boas-vindas e Setup", "data_limite": date(2026, 3, 27), "responsaveis": "Alice Mendonça, Bruno Tavares", "qtd_responsaveis": 2, "situacao": "entregue"},
            {"titulo": "Lógica Digital", "data_limite": date(2026, 4, 6), "responsaveis": "Camila Rezende, Diego Fonseca", "qtd_responsaveis": 2, "situacao": "entregue"},
            {"titulo": "Python: Entradas e Saídas", "data_limite": date(2026, 4, 16), "responsaveis": "Elisa Drummond, Felipe Quaresma", "qtd_responsaveis": 2, "situacao": "entregue"},
            {"titulo": "Python: Condicionais e Laços", "data_limite": date(2026, 5, 4), "responsaveis": "Gabriela Monteiro, Henrique Lacerda", "qtd_responsaveis": 2, "situacao": "atraso"},
        ],
        "padrinhos_por_turno": [
            {"turno": "Manhã", "qtd": 5, "nomes": ["Alice Mendonça", "Camila Rezende", "Elisa Drummond", "Gabriela Monteiro", "Isabela Coutinho"]},
            {"turno": "Noite", "qtd": 5, "nomes": ["Bruno Tavares", "Diego Fonseca", "Felipe Quaresma", "Henrique Lacerda", "João Vasconcelos"]},
        ],
        "total_aptos_acg": 8,
        "total_nao_aptos": 2,
        "taxa_aptidao": 80,
        "total_aprovados": 7,
        "total_alerta": 1,
        "total_reprovados": 1,
        "total_reportados": 1,
        "turno_data": [
            {"turno": "Manhã", "qtd": 5, "pct": 50},
            {"turno": "Noite", "qtd": 5, "pct": 50},
        ],
        "turno_data_cal": [
            {"turno": "Manhã", "qtd": 10, "pct": 50},
            {"turno": "Noite", "qtd": 10, "pct": 50},
        ],
        "pct_bolsista": 30,
        "pct_bh": 60,
        "pct_trabalha": 50,
        "pct_bolsista_cal": 35,
        "pct_bh_cal": 55,
        "pct_trabalha_cal": 30,
    }

    ctx_certificado = {
        "estatico": True,
        "padrinho": aprovados[0],
        "total_padrinhos": 10,
        "total_calouros": 20,
        "semestre": config["semestre"],
        "config": config,
        "hoje": hoje,
        "funcao_certificado": {
            "titulo": "Madrinha",
            "texto": "madrinha",
        },
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
