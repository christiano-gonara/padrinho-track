import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "mentoria.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS padrinhos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nome        TEXT NOT NULL,
        matricula   TEXT UNIQUE NOT NULL,
        email       TEXT,
        telefone    TEXT,
        turno       TEXT,
        ativo       INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS reunioes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        data        TEXT NOT NULL,
        tema        TEXT,
        descricao   TEXT
    );

    CREATE TABLE IF NOT EXISTS presencas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        reuniao_id  INTEGER NOT NULL,
        padrinho_id INTEGER NOT NULL,
        presente    INTEGER DEFAULT 0,
        justificada INTEGER DEFAULT 0,
        FOREIGN KEY (reuniao_id)  REFERENCES reunioes(id),
        FOREIGN KEY (padrinho_id) REFERENCES padrinhos(id),
        UNIQUE (reuniao_id, padrinho_id)
    );

    CREATE TABLE IF NOT EXISTS temas (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo        TEXT NOT NULL,
        data_aviso    TEXT,
        data_limite   TEXT NOT NULL,
        data_entrega  TEXT,
        situacao      TEXT DEFAULT 'pendente'
    );

    CREATE TABLE IF NOT EXISTS tema_padrinhos (
        tema_id     INTEGER NOT NULL,
        padrinho_id INTEGER NOT NULL,
        PRIMARY KEY (tema_id, padrinho_id),
        FOREIGN KEY (tema_id)     REFERENCES temas(id),
        FOREIGN KEY (padrinho_id) REFERENCES padrinhos(id)
    );

    CREATE TABLE IF NOT EXISTS advertencias (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        padrinho_id INTEGER NOT NULL,
        tipo        TEXT NOT NULL,
        origem      TEXT NOT NULL,
        motivo      TEXT,
        data        TEXT NOT NULL,
        FOREIGN KEY (padrinho_id) REFERENCES padrinhos(id)
    );

    CREATE TABLE IF NOT EXISTS calouros (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT NOT NULL,
        telefone  TEXT
    );

    CREATE TABLE IF NOT EXISTS matches (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        padrinho_id INTEGER NOT NULL,
        calouro_id  INTEGER NOT NULL,
        FOREIGN KEY (padrinho_id) REFERENCES padrinhos(id),
        FOREIGN KEY (calouro_id)  REFERENCES calouros(id),
        UNIQUE (padrinho_id, calouro_id)
    );

    CREATE TABLE IF NOT EXISTS config (
        chave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    );

    INSERT OR IGNORE INTO config (chave, valor) VALUES ('limite_amarelos', '2');
    """)
    conn.commit()
    conn.close()