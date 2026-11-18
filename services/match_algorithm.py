from database import get_conn


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
