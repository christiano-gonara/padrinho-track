import csv
import io
import math

from backend.database import get_conn
from backend.models import get_calouros_match_completo, registrar_log
from backend.repositories import match_repository, padrinho_repository


def rodar_match(max_calouros=3, score_minimo=0):
    """Executa o algoritmo de compatibilidade entre padrinhos e calouros."""
    conn = get_conn()
    padrinhos = [dict(p) for p in conn.execute(
        "SELECT * FROM padrinhos WHERE ativo=1 ORDER BY nome"
    ).fetchall()]
    calouros = [dict(c) for c in conn.execute(
        "SELECT * FROM calouros ORDER BY nome"
    ).fetchall()]
    conn.close()

    def _score(p, c):
        score = 0
        if p.get("turno") and c.get("turno") and p["turno"] == c["turno"]:
            score += 200
        if p.get("genero") and c.get("genero") and p["genero"] == c["genero"]:
            score += 80
        if p.get("cidade_bh") and c.get("cidade_bh"):
            score += 4
        if p.get("bolsista") and c.get("bolsista"):
            score += 2
        if p.get("trabalha") and c.get("trabalha"):
            score += 1
        idade_padrinho, idade_calouro = p.get("idade"), c.get("idade")
        if idade_padrinho and idade_calouro:
            diff = abs(int(idade_padrinho) - int(idade_calouro))
            if diff <= 2:
                score += 8
            elif diff <= 5:
                score += 4
        return score

    atribuicoes = {p["id"]: [] for p in padrinhos}
    sem_match = []

    for calouro in calouros:
        candidatos = []
        for padrinho in padrinhos:
            quantidade_atual = len(atribuicoes[padrinho["id"]])
            if quantidade_atual >= max_calouros:
                continue
            score = _score(padrinho, calouro) - quantidade_atual * 10
            candidatos.append((score, padrinho))

        if not candidatos:
            sem_match.append({"calouro": calouro, "motivo": "Sem vagas disponíveis"})
            continue

        candidatos.sort(key=lambda item: -item[0])
        melhor_score, melhor_padrinho = candidatos[0]

        if melhor_score < score_minimo:
            sem_match.append({"calouro": calouro, "motivo": f"Score {melhor_score} abaixo do mínimo configurado"})
            continue

        atribuicoes[melhor_padrinho["id"]].append({"calouro": calouro, "score": melhor_score})

    resultado = [
        {
            "padrinho": padrinho,
            "calouros": atribuicoes[padrinho["id"]],
            "total": len(atribuicoes[padrinho["id"]]),
            "score_medio": round(
                sum(item["score"] for item in atribuicoes[padrinho["id"]]) / len(atribuicoes[padrinho["id"]])
            ) if atribuicoes[padrinho["id"]] else 0,
        }
        for padrinho in padrinhos
    ]
    return {"resultado": resultado, "sem_match": sem_match}


def listar_calouros_com_match():
    """Lista padrinhos ativos com seus calouros atribuídos."""
    return get_calouros_match_completo()


def montar_contexto_match():
    """Monta dados e métricas para a tela de match padrinho-calouro."""
    dados = get_calouros_match_completo()
    return {
        "dados": dados,
        "total_matches": match_repository.contar_matches(),
        "total_calouros": match_repository.contar_calouros(),
        "total_padrinhos": padrinho_repository.contar_ativos(),
    }


def gerar_e_confirmar_match():
    """Executa o algoritmo de match e grava o resultado como distribuição oficial."""
    total_calouros = match_repository.contar_calouros()
    total_padrinhos = padrinho_repository.contar_ativos()
    max_calouros = math.ceil(total_calouros / max(total_padrinhos, 1))
    resultado = rodar_match(max_calouros=max_calouros, score_minimo=0)

    match_repository.substituir_matches(resultado)
    total = sum(len(g["calouros"]) for g in resultado["resultado"])
    registrar_log("MATCH_GERADO", f"{total} matches gerados automaticamente.")
    return total


def resetar_match():
    """Remove todos os vínculos de match existentes."""
    match_repository.apagar_todos()
    registrar_log("MATCH_RESETADO", "Todos os matches foram removidos.")


def listar_contatos_match():
    """Lista contatos no formato usado pela página de contatos do match."""
    return match_repository.listar_contatos()


def gerar_csv_lista_contatos():
    """Gera o CSV da lista de contatos padrinho-calouro."""
    rows = listar_contatos_match()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Padrinho", "Turno", "Calouro", "Telefone do Calouro"])
    for row in rows:
        writer.writerow([row["padrinho_nome"], row["turno"] or "—", row["calouro_nome"], row["telefone"] or "—"])
    return buf.getvalue().encode("utf-8-sig")
