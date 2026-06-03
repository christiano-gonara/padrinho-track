import os
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "mentoria.db"


# ── PostgreSQL row/connection wrappers ──────────────────────────────────────

class _PgRow:
    """Wraps a psycopg2 tuple row with sqlite3.Row-compatible index+key access."""
    __slots__ = ("_data", "_keys")

    def __init__(self, data, description):
        self._data = data
        self._keys = [d[0] for d in description]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        return self._data[self._keys.index(key)]

    def __iter__(self):
        return iter(self._data)

    def __bool__(self):
        return True

    def keys(self):
        return self._keys


class _PgCursorResult:
    """Cursor result returned by _PgConn.execute() — supports fetchone/fetchall/lastrowid."""

    def __init__(self, cur, pg_conn):
        self._cur  = cur
        self._conn = pg_conn
        self._desc = cur.description

    def _wrap(self, row):
        return None if row is None else _PgRow(row, self._desc)

    def fetchone(self):
        return self._wrap(self._cur.fetchone())

    def fetchall(self):
        if not self._desc:
            return []
        return [_PgRow(r, self._desc) for r in self._cur.fetchall()]

    @property
    def lastrowid(self):
        c = self._conn.cursor()
        c.execute("SELECT lastval()")
        val = c.fetchone()[0]
        c.close()
        return val


# ── SQL dialect translation (SQLite → PostgreSQL) ───────────────────────────

_RE_QMARK      = re.compile(r'\?')
_RE_OR_IGNORE  = re.compile(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b', re.IGNORECASE)
_RE_OR_REPLACE = re.compile(
    r'\bINSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)',
    re.IGNORECASE | re.DOTALL,
)


def _translate_sql(sql):
    sql = _RE_QMARK.sub('%s', sql)
    if _RE_OR_IGNORE.search(sql):
        sql = _RE_OR_IGNORE.sub('INSERT INTO', sql)
        return sql.rstrip('; \n') + ' ON CONFLICT DO NOTHING'
    m = _RE_OR_REPLACE.search(sql)
    if m:
        table, cols_s, vals_s = m.group(1), m.group(2), m.group(3)
        cols = [c.strip() for c in cols_s.split(',')]
        updates = ', '.join(f'{c} = EXCLUDED.{c}' for c in cols[1:])
        return (f'INSERT INTO {table} ({cols_s}) VALUES ({vals_s}) '
                f'ON CONFLICT ({cols[0]}) DO UPDATE SET {updates}')
    return sql


class _PgConn:
    """psycopg2 connection wrapper with a sqlite3-compatible API."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(_translate_sql(sql), params or ())
        return _PgCursorResult(cur, self._conn)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# ── Public API ──────────────────────────────────────────────────────────────

def get_conn():
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        import psycopg2
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return _PgConn(psycopg2.connect(db_url))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    print("DATABASE_URL exists:", bool(os.environ.get("DATABASE_URL")))
    print("Calling:", "PostgreSQL" if os.environ.get("DATABASE_URL") else "SQLite")
    if os.environ.get("DATABASE_URL", ""):
        _init_pg()
    else:
        _init_sqlite()


# ── SQLite initialisation ────────────────────────────────────────────────────

def _init_sqlite():
    conn = sqlite3.connect(DB_PATH)
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

    CREATE INDEX IF NOT EXISTS idx_advertencias_padrinho ON advertencias(padrinho_id);
    CREATE INDEX IF NOT EXISTS idx_presencas_padrinho    ON presencas(padrinho_id);
    CREATE INDEX IF NOT EXISTS idx_presencas_reuniao     ON presencas(reuniao_id);
    CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_tema   ON tema_padrinhos(tema_id);
    CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_padrinho ON tema_padrinhos(padrinho_id);
    CREATE INDEX IF NOT EXISTS idx_logs_data             ON logs(data DESC);
    """)
    conn.commit()

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
        "ALTER TABLE padrinhos ADD COLUMN periodo TEXT",
        "ALTER TABLE padrinhos ADD COLUMN passou_algoritmos INTEGER DEFAULT NULL",
        "ALTER TABLE calouros ADD COLUMN primeiro_periodo INTEGER DEFAULT NULL",
        "ALTER TABLE padrinhos RENAME COLUMN prouni TO bolsista",
        "ALTER TABLE calouros RENAME COLUMN prouni TO bolsista",
    ]
    for sql in _migracoes:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


# ── PostgreSQL initialisation ────────────────────────────────────────────────

_PG_SCHEMA = [
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

# Applied on top of the full schema to handle DBs created before certain columns existed.
_PG_MIGRACOES = [
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
    # Rename prouni→bolsista for DBs created before this migration; ignore if already done.
    """DO $$ BEGIN
         ALTER TABLE padrinhos RENAME COLUMN prouni TO bolsista;
       EXCEPTION WHEN undefined_column OR duplicate_column THEN NULL;
       END $$""",
    """DO $$ BEGIN
         ALTER TABLE calouros RENAME COLUMN prouni TO bolsista;
       EXCEPTION WHEN undefined_column OR duplicate_column THEN NULL;
       END $$""",
]


def _init_pg():
    import psycopg2
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    for stmt in _PG_SCHEMA:
        cur.execute(stmt)
    conn.commit()
    for sql in _PG_MIGRACOES:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
