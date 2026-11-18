import csv
import io
import math

from models import get_calouros_match_completo, registrar_log
from repositories import calouro_repository, match_repository, padrinho_repository
from services.match_algorithm import rodar_match


def montar_contexto_match():
    """Monta dados e métricas para a tela de match padrinho-calouro."""
    dados = get_calouros_match_completo()
    return {
        "dados": dados,
        "total_matches": match_repository.contar_matches(),
        "total_calouros": calouro_repository.contar_todos(),
        "total_padrinhos": padrinho_repository.contar_ativos(),
    }


def gerar_e_confirmar_match():
    """Executa o algoritmo de match e grava o resultado como distribuição oficial."""
    total_calouros = calouro_repository.contar_todos()
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
