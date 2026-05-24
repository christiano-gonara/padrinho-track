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

    CREATE TABLE IF NOT EXISTS logs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        acao        TEXT NOT NULL,
        descricao   TEXT,
        data        TEXT NOT NULL,
        ip          TEXT
    );

    INSERT OR IGNORE INTO config (chave, valor) VALUES ('limite_amarelos', '2');

    CREATE INDEX IF NOT EXISTS idx_advertencias_padrinho ON advertencias(padrinho_id);
    CREATE INDEX IF NOT EXISTS idx_presencas_padrinho ON presencas(padrinho_id);
    CREATE INDEX IF NOT EXISTS idx_presencas_reuniao ON presencas(reuniao_id);
    CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_tema ON tema_padrinhos(tema_id);
    CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_padrinho ON tema_padrinhos(padrinho_id);
    """)
    conn.commit()

    # Migrações incrementais — colunas adicionadas depois da criação inicial
    _migracoes = [
        "ALTER TABLE padrinhos ADD COLUMN genero TEXT",
        "ALTER TABLE padrinhos ADD COLUMN idade INTEGER",
        "ALTER TABLE padrinhos ADD COLUMN cidade_bh INTEGER DEFAULT 0",
        "ALTER TABLE padrinhos ADD COLUMN prouni INTEGER DEFAULT 0",
        "ALTER TABLE padrinhos ADD COLUMN trabalha INTEGER DEFAULT 0",
        "ALTER TABLE calouros ADD COLUMN turno TEXT",
        "ALTER TABLE calouros ADD COLUMN genero TEXT",
        "ALTER TABLE calouros ADD COLUMN idade INTEGER",
        "ALTER TABLE calouros ADD COLUMN cidade_bh INTEGER DEFAULT 0",
        "ALTER TABLE calouros ADD COLUMN prouni INTEGER DEFAULT 0",
        "ALTER TABLE calouros ADD COLUMN trabalha INTEGER DEFAULT 0",
    ]
    for sql in _migracoes:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # coluna já existe
    conn.commit()
    conn.close()