SQLITE_SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_advertencias_padrinho ON advertencias(padrinho_id);
CREATE INDEX IF NOT EXISTS idx_presencas_padrinho    ON presencas(padrinho_id);
CREATE INDEX IF NOT EXISTS idx_presencas_reuniao     ON presencas(reuniao_id);
CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_tema   ON tema_padrinhos(tema_id);
CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_padrinho ON tema_padrinhos(padrinho_id);
CREATE INDEX IF NOT EXISTS idx_logs_data             ON logs(data DESC);
"""

SQLITE_MIGRACOES = [
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
    "ALTER TABLE padrinhos ADD COLUMN periodo TEXT",
    "ALTER TABLE padrinhos ADD COLUMN passou_algoritmos INTEGER DEFAULT NULL",
    "ALTER TABLE calouros ADD COLUMN primeiro_periodo INTEGER DEFAULT NULL",
    "ALTER TABLE padrinhos RENAME COLUMN prouni TO bolsista",
    "ALTER TABLE calouros RENAME COLUMN prouni TO bolsista",
]

PG_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS padrinhos (
        id                SERIAL PRIMARY KEY,
        nome              TEXT NOT NULL,
        matricula         TEXT UNIQUE NOT NULL,
        email             TEXT,
        telefone          TEXT,
        turno             TEXT,
        ativo             INTEGER DEFAULT 1,
        genero            TEXT,
        idade             INTEGER,
        cidade_bh         INTEGER DEFAULT 0,
        bolsista          INTEGER DEFAULT 0,
        trabalha          INTEGER DEFAULT 0,
        periodo           TEXT,
        passou_algoritmos INTEGER DEFAULT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS reunioes (
        id        SERIAL PRIMARY KEY,
        data      TEXT NOT NULL,
        tema      TEXT,
        descricao TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS presencas (
        id          SERIAL PRIMARY KEY,
        reuniao_id  INTEGER NOT NULL REFERENCES reunioes(id),
        padrinho_id INTEGER NOT NULL REFERENCES padrinhos(id),
        presente    INTEGER DEFAULT 0,
        justificada INTEGER DEFAULT 0,
        UNIQUE (reuniao_id, padrinho_id)
    )""",
    """CREATE TABLE IF NOT EXISTS temas (
        id           SERIAL PRIMARY KEY,
        titulo       TEXT NOT NULL,
        data_aviso   TEXT,
        data_limite  TEXT NOT NULL,
        data_entrega TEXT,
        situacao     TEXT DEFAULT 'pendente'
    )""",
    """CREATE TABLE IF NOT EXISTS tema_padrinhos (
        tema_id     INTEGER NOT NULL REFERENCES temas(id),
        padrinho_id INTEGER NOT NULL REFERENCES padrinhos(id),
        PRIMARY KEY (tema_id, padrinho_id)
    )""",
    """CREATE TABLE IF NOT EXISTS advertencias (
        id          SERIAL PRIMARY KEY,
        padrinho_id INTEGER NOT NULL REFERENCES padrinhos(id),
        tipo        TEXT NOT NULL,
        origem      TEXT NOT NULL,
        motivo      TEXT,
        data        TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS calouros (
        id               SERIAL PRIMARY KEY,
        nome             TEXT NOT NULL,
        telefone         TEXT,
        turno            TEXT,
        genero           TEXT,
        idade            INTEGER,
        cidade_bh        INTEGER DEFAULT 0,
        bolsista         INTEGER DEFAULT 0,
        trabalha         INTEGER DEFAULT 0,
        primeiro_periodo INTEGER DEFAULT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS matches (
        id          SERIAL PRIMARY KEY,
        padrinho_id INTEGER NOT NULL REFERENCES padrinhos(id),
        calouro_id  INTEGER NOT NULL REFERENCES calouros(id),
        UNIQUE (padrinho_id, calouro_id)
    )""",
    """CREATE TABLE IF NOT EXISTS config (
        chave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS logs (
        id        SERIAL PRIMARY KEY,
        acao      TEXT NOT NULL,
        descricao TEXT,
        data      TEXT NOT NULL,
        ip        TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_advertencias_padrinho   ON advertencias(padrinho_id)",
    "CREATE INDEX IF NOT EXISTS idx_presencas_padrinho      ON presencas(padrinho_id)",
    "CREATE INDEX IF NOT EXISTS idx_presencas_reuniao       ON presencas(reuniao_id)",
    "CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_tema     ON tema_padrinhos(tema_id)",
    "CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_padrinho ON tema_padrinhos(padrinho_id)",
    "CREATE INDEX IF NOT EXISTS idx_logs_data               ON logs(data DESC)",
]

PG_MIGRACOES = [
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS genero TEXT",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS idade INTEGER",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS cidade_bh INTEGER DEFAULT 0",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS bolsista INTEGER DEFAULT 0",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS trabalha INTEGER DEFAULT 0",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS periodo TEXT",
    "ALTER TABLE padrinhos ADD COLUMN IF NOT EXISTS passou_algoritmos INTEGER DEFAULT NULL",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS turno TEXT",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS genero TEXT",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS idade INTEGER",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS cidade_bh INTEGER DEFAULT 0",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS bolsista INTEGER DEFAULT 0",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS trabalha INTEGER DEFAULT 0",
    "ALTER TABLE calouros ADD COLUMN IF NOT EXISTS primeiro_periodo INTEGER DEFAULT NULL",
    """DO $$ BEGIN
         ALTER TABLE padrinhos RENAME COLUMN prouni TO bolsista;
       EXCEPTION WHEN undefined_column OR duplicate_column THEN NULL;
       END $$""",
    """DO $$ BEGIN
         ALTER TABLE calouros RENAME COLUMN prouni TO bolsista;
       EXCEPTION WHEN undefined_column OR duplicate_column THEN NULL;
       END $$""",
]
