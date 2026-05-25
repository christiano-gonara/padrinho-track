# =============================================================
# SEED DE EXEMPLO — DADOS FICTÍCIOS
# =============================================================
# Este script popula o banco com dados de demonstração.
# Todos os nomes, matrículas, emails e telefones são fictícios
# e foram criados apenas para fins de teste e portfólio.
#
# Para rodar (da raiz do projeto):
#   python scripts/seed_exemplo.py
# =============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import init_db, get_conn
from datetime import date

PADRINHOS = [
    ("Alice Mendonça",       "100001", "alice.mendonca@exemplo.com",    "31900000001", "Manhã"),
    ("Bruno Tavares",        "100002", "bruno.tavares@exemplo.com",     "31900000002", "Noite"),
    ("Camila Rezende",       "100003", "camila.rezende@exemplo.com",    "31900000003", "Manhã"),
    ("Diego Fonseca",        "100004", "diego.fonseca@exemplo.com",     "31900000004", "Noite"),
    ("Elisa Drummond",       "100005", "elisa.drummond@exemplo.com",    "31900000005", "Manhã"),
    ("Felipe Quaresma",      "100006", "felipe.quaresma@exemplo.com",   "31900000006", "Noite"),
    ("Gabriela Monteiro",    "100007", "gabriela.monteiro@exemplo.com", "31900000007", "Manhã"),
    ("Henrique Lacerda",     "100008", "henrique.lacerda@exemplo.com",  "31900000008", "Noite"),
    ("Isabela Coutinho",     "100009", "isabela.coutinho@exemplo.com",  "31900000009", "Manhã"),
    ("João Vasconcelos",     "100010", "joao.vasconcelos@exemplo.com",  "31900000010", "Noite"),
]

CALOUROS = [
    ("Mateus Aguiar",        "31900001001"),
    ("Larissa Peixoto",      "31900001002"),
    ("Rafael Evangelista",   "31900001003"),
    ("Beatriz Salomão",      "31900001004"),
    ("Lucas Wanderley",      "31900001005"),
    ("Fernanda Azevedo",     "31900001006"),
    ("Pedro Magalhães",      "31900001007"),
    ("Julia Paranhos",       "31900001008"),
    ("Guilherme Pacheco",    "31900001009"),
    ("Amanda Vilela",        "31900001010"),
    ("Thiago Brandão",       "31900001011"),
    ("Carolina Salgado",     "31900001012"),
    ("Vitor Sepúlveda",      "31900001013"),
    ("Mariana Toledo",       "31900001014"),
    ("Leonardo Bittencourt", "31900001015"),
    ("Stephanie Caldeira",   "31900001016"),
    ("André Mascarenhas",    "31900001017"),
    ("Natalia Veríssimo",    "31900001018"),
    ("Diego Canellas",       "31900001019"),
    ("Priscila Uchôa",       "31900001020"),
]

TEMAS = [
    ("Boas vindas e Setup",         "2026-03-23", "2026-03-27", [0, 1, 2]),
    ("Lógica digital",              "2026-03-27", "2026-04-06", [3, 4, 5]),
    ("Python 1: Entradas e saídas", "2026-04-06", "2026-04-09", [6, 7, 8]),
    ("Python 2: Condicionais",      "2026-04-10", "2026-04-16", [9, 0, 1]),
    ("Base numérica: conversão",    "2026-04-17", "2026-04-23", [2, 3, 4]),
]

def seed():
    init_db()
    conn = get_conn()

    # Padrinhos
    padrinho_ids = []
    for nome, matricula, email, telefone, turno in PADRINHOS:
        try:
            cur = conn.execute(
                "INSERT INTO padrinhos (nome, matricula, email, telefone, turno) VALUES (?,?,?,?,?)",
                (nome, matricula, email, telefone, turno)
            )
            padrinho_ids.append(cur.lastrowid)
        except Exception:
            row = conn.execute("SELECT id FROM padrinhos WHERE matricula=?", (matricula,)).fetchone()
            padrinho_ids.append(row["id"])
    print(f"[OK] {len(padrinho_ids)} padrinhos inseridos.")

    # Calouros e matches
    for i, (nome, telefone) in enumerate(CALOUROS):
        cur = conn.execute(
            "INSERT INTO calouros (nome, telefone) VALUES (?,?)",
            (nome, telefone)
        )
        calouro_id = cur.lastrowid
        padrinho_id = padrinho_ids[i % len(padrinho_ids)]
        conn.execute(
            "INSERT OR IGNORE INTO matches (padrinho_id, calouro_id) VALUES (?,?)",
            (padrinho_id, calouro_id)
        )
    print(f"[OK] {len(CALOUROS)} calouros e matches inseridos.")

    # Reuniões
    reuniao_ids = []
    reunioes = [
        ("2026-03-20", "Abertura do semestre",  "Reunião inaugural"),
        ("2026-04-03", "Python básico",         "Revisão dos primeiros temas"),
        ("2026-04-17", "Dúvidas e alinhamento", "Reunião de meio de semestre"),
    ]
    for data, tema, descricao in reunioes:
        cur = conn.execute(
            "INSERT INTO reunioes (data, tema, descricao) VALUES (?,?,?)",
            (data, tema, descricao)
        )
        reuniao_ids.append(cur.lastrowid)
    print(f"[OK] {len(reuniao_ids)} reuniões inseridas.")

    # Presenças — simula ausências variadas
    ausencias = {
        reuniao_ids[0]: [padrinho_ids[2], padrinho_ids[7]],
        reuniao_ids[1]: [padrinho_ids[4]],
        reuniao_ids[2]: [padrinho_ids[2], padrinho_ids[4], padrinho_ids[9]],
    }
    for reuniao_id in reuniao_ids:
        for pid in padrinho_ids:
            presente = 0 if pid in ausencias.get(reuniao_id, []) else 1
            conn.execute("""
                INSERT OR IGNORE INTO presencas (reuniao_id, padrinho_id, presente, justificada)
                VALUES (?,?,?,0)
            """, (reuniao_id, pid, presente))

    # Advertências automáticas por falta
    for reuniao_id, ausentes in ausencias.items():
        for pid in ausentes:
            conn.execute("""
                INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
                VALUES (?, 'amarelo', 'falta', 'Falta sem justificativa', ?)
            """, (pid, date.today().isoformat()))
    print("[OK] Presenças e advertências por falta inseridas.")

    # Advertência manual — vermelho exemplo
    conn.execute("""
        INSERT INTO advertencias (padrinho_id, tipo, origem, motivo, data)
        VALUES (?, 'vermelho', 'manual', 'Comportamento inadequado — exemplo', ?)
    """, (padrinho_ids[9], date.today().isoformat()))
    print("[OK] Advertência manual inserida.")

    # Temas
    for titulo, data_aviso, data_limite, indices in TEMAS:
        cur = conn.execute(
            "INSERT INTO temas (titulo, data_aviso, data_limite) VALUES (?,?,?)",
            (titulo, data_aviso, data_limite)
        )
        tema_id = cur.lastrowid
        for i in indices:
            conn.execute(
                "INSERT OR IGNORE INTO tema_padrinhos (tema_id, padrinho_id) VALUES (?,?)",
                (tema_id, padrinho_ids[i])
            )
    print(f"[OK] {len(TEMAS)} temas inseridos.")

    conn.commit()
    conn.close()
    print("\n[OK] Seed de exemplo concluído!")
    print("   Acesse http://127.0.0.1:5000 para ver o sistema populado.")

if __name__ == "__main__":
    seed()