import os
import re
import sqlite3
from pathlib import Path

from database_schema import PG_MIGRACOES, PG_SCHEMA, SQLITE_MIGRACOES, SQLITE_SCHEMA

DB_PATH = Path(__file__).parent / "instance" / "mentoria.db"


class _PgRow:
    """Adapta linhas do psycopg2 para acesso parecido com sqlite3.Row."""

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
    """Resultado de cursor PostgreSQL com API próxima da usada no SQLite."""

    def __init__(self, cur, pg_conn):
        self._cur = cur
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


_RE_QMARK = re.compile(r"\?")
_RE_OR_IGNORE = re.compile(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", re.IGNORECASE)
_RE_OR_REPLACE = re.compile(
    r"\bINSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
    re.IGNORECASE | re.DOTALL,
)


def _translate_sql(sql):
    """Traduz pequenos trechos SQL do SQLite para o PostgreSQL."""
    sql = _RE_QMARK.sub("%s", sql)
    if _RE_OR_IGNORE.search(sql):
        sql = _RE_OR_IGNORE.sub("INSERT INTO", sql)
        return sql.rstrip("; \n") + " ON CONFLICT DO NOTHING"

    m = _RE_OR_REPLACE.search(sql)
    if m:
        table, cols_s, vals_s = m.group(1), m.group(2), m.group(3)
        cols = [c.strip() for c in cols_s.split(",")]
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols[1:])
        return (
            f"INSERT INTO {table} ({cols_s}) VALUES ({vals_s}) "
            f"ON CONFLICT ({cols[0]}) DO UPDATE SET {updates}"
        )
    return sql


class _PgConn:
    """Wrapper para usar PostgreSQL com a mesma chamada simples de get_conn()."""

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


def get_conn():
    """Abre conexão SQLite local ou PostgreSQL quando DATABASE_URL existir."""
    db_url = _postgres_url()
    if db_url:
        import psycopg2
        return _PgConn(psycopg2.connect(db_url))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria tabelas e aplica migrações do banco configurado."""
    print("DATABASE_URL exists:", bool(os.environ.get("DATABASE_URL")))
    print("Calling:", "PostgreSQL" if os.environ.get("DATABASE_URL") else "SQLite")
    if os.environ.get("DATABASE_URL", ""):
        _init_pg()
    else:
        _init_sqlite()


def _postgres_url():
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url


def _init_sqlite():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SQLITE_SCHEMA)
    conn.commit()

    for sql in SQLITE_MIGRACOES:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def _init_pg():
    import psycopg2

    conn = psycopg2.connect(_postgres_url())
    cur = conn.cursor()
    for stmt in PG_SCHEMA:
        cur.execute(stmt)
    conn.commit()

    for sql in PG_MIGRACOES:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
