from datetime import date

from repositories import advertencia_repository, presenca_repository, reuniao_repository


def _contar_reunioes():
    return reuniao_repository.contar_todas()

def emitir_advertencias_falta(reuniao_id):
    """Emite amarelo para ausências sem justificativa de uma reunião."""
    ausentes = presenca_repository.listar_ausentes_sem_justificativa(reuniao_id)
    motivo = f"Falta sem justificativa — reunião {reuniao_id}"
    registros = []
    for row in ausentes:
        existente = advertencia_repository.buscar_existente(row["padrinho_id"], motivo)
        if not existente:
            registros.append((row["padrinho_id"], "amarelo", "falta", motivo, date.today().isoformat()))
    advertencia_repository.criar_varias(registros)

def emitir_advertencia_manual(padrinho_id, motivo, tipo='vermelho'):
    """Emite uma advertência manual."""
    advertencia_repository.criar(padrinho_id, tipo, "manual", motivo)

def get_advertencias_padrinho(padrinho_id):
    return advertencia_repository.listar_por_padrinho(padrinho_id)

def calcular_status(padrinho_id, limite=None):
    rows = advertencia_repository.contar_por_tipo_padrinho(padrinho_id)
    counts = {r["tipo"]: r["cnt"] for r in rows}
    amarelos = counts.get("amarelo", 0)
    vermelhos = counts.get("vermelho", 0)

    if limite is None:
        limite = _contar_reunioes()

    if vermelhos >= 1:
        return {"status": "inapto_vermelho", "amarelos": amarelos, "vermelhos": vermelhos}
    if limite > 0 and amarelos >= limite:
        return {"status": "inapto_amarelo", "amarelos": amarelos, "vermelhos": vermelhos}
    if limite > 0 and amarelos == limite - 1:
        return {"status": "alerta", "amarelos": amarelos, "vermelhos": vermelhos}
    return {"status": "apto", "amarelos": amarelos, "vermelhos": vermelhos}

def calcular_todos_status(padrinho_ids, limite=None):
    """Calcula status em lote para evitar uma consulta por padrinho."""
    if not padrinho_ids:
        return {}
    if limite is None:
        limite = _contar_reunioes()
    rows = advertencia_repository.contar_por_tipo_padrinhos(padrinho_ids)
    counts = {}
    for r in rows:
        pid = r["padrinho_id"]
        if pid not in counts:
            counts[pid] = {}
        counts[pid][r["tipo"]] = r["cnt"]
    result = {}
    for pid in padrinho_ids:
        c = counts.get(pid, {})
        amarelos  = c.get("amarelo", 0)
        vermelhos = c.get("vermelho", 0)
        if vermelhos >= 1:
            status = "inapto_vermelho"
        elif limite > 0 and amarelos >= limite:
            status = "inapto_amarelo"
        elif limite > 0 and amarelos == limite - 1:
            status = "alerta"
        else:
            status = "apto"
        result[pid] = {"status": status, "amarelos": amarelos, "vermelhos": vermelhos}
    return result
