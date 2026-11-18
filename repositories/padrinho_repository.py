from database import get_conn


def listar_ativos():
    """Busca padrinhos ativos ordenados por nome."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM padrinhos WHERE ativo = 1 ORDER BY nome").fetchall()
    conn.close()
    return rows


def buscar_por_id(padrinho_id):
    """Busca um padrinho pelo ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM padrinhos WHERE id = ?", (padrinho_id,)).fetchone()
    conn.close()
    return row


def contar_ativos():
    """Conta padrinhos ativos."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM padrinhos WHERE ativo=1").fetchone()[0]
    conn.close()
    return total


def listar_ativos_id_nome_exceto(padrinho_id):
    """Lista padrinhos ativos para redistribuição, excluindo o atual."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, nome FROM padrinhos WHERE ativo=1 AND id != ? ORDER BY nome",
        (padrinho_id,),
    ).fetchall()
    conn.close()
    return rows


def listar_calouros_do_padrinho(padrinho_id):
    """Lista calouros atualmente vinculados a um padrinho."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.id, c.nome, c.telefone
        FROM matches m JOIN calouros c ON c.id = m.calouro_id
        WHERE m.padrinho_id = ?
        ORDER BY c.nome
    """, (padrinho_id,)).fetchall()
    conn.close()
    return rows


def listar_matriculas():
    """Lista matrículas cadastradas de padrinhos."""
    conn = get_conn()
    rows = conn.execute("SELECT matricula FROM padrinhos").fetchall()
    conn.close()
    return rows


def cadastrar(nome, matricula, email, telefone, turno):
    """Cadastra um padrinho."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO padrinhos (nome, matricula, email, telefone, turno) VALUES (?, ?, ?, ?, ?)",
        (nome, matricula, email, telefone, turno),
    )
    conn.commit()
    conn.close()


def atualizar(padrinho_id, nome, matricula, email, telefone, turno,
              genero=None, idade=None, cidade_bh=None, bolsista=None,
              trabalha=None, periodo=None, passou_algoritmos=None):
    """Atualiza dados cadastrais e demográficos de um padrinho."""
    conn = get_conn()
    conn.execute("""
        UPDATE padrinhos
        SET nome=?, matricula=?, email=?, telefone=?, turno=?,
            genero=?, idade=?, cidade_bh=?, bolsista=?, trabalha=?,
            periodo=?, passou_algoritmos=?
        WHERE id=?
    """, (nome, matricula, email, telefone, turno,
          genero, idade, cidade_bh, bolsista, trabalha,
          periodo, passou_algoritmos, padrinho_id))
    conn.commit()
    conn.close()


def desativar(padrinho_id):
    """Marca um padrinho como inativo."""
    conn = get_conn()
    conn.execute("UPDATE padrinhos SET ativo=0 WHERE id=?", (padrinho_id,))
    conn.commit()
    conn.close()


def redistribuir_calouros_e_desativar(padrinho_id, redistribuicao):
    """Redistribui vínculos de calouros e desativa o padrinho original."""
    conn = get_conn()
    for calouro_id, novo_padrinho_id in redistribuicao.items():
        if novo_padrinho_id:
            conn.execute(
                "UPDATE matches SET padrinho_id=? WHERE calouro_id=? AND padrinho_id=?",
                (int(novo_padrinho_id), int(calouro_id), padrinho_id),
            )
        else:
            conn.execute(
                "DELETE FROM matches WHERE calouro_id=? AND padrinho_id=?",
                (int(calouro_id), padrinho_id),
            )
    conn.execute("UPDATE padrinhos SET ativo=0 WHERE id=?", (padrinho_id,))
    conn.commit()
    conn.close()
