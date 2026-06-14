"""SQLite connection and schema initialisation."""
import sqlite3
from pathlib import Path

# schema.sql sits at the project root (two levels up from this package).
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema.sql"
DEFAULT_DB = Path("techwatch.db")


def connect(db_path=DEFAULT_DB):
    """Open a connection with foreign keys on and dict-like rows."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create tables from schema.sql if they do not exist yet, then migrate."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    _migrate(conn)
    conn.commit()


def _migrate(conn):
    """Bring older databases up to date with the current schema."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(article_tags)")}
    if "tagged_at" not in cols:
        # ALTER cannot use a non-constant default, so add the column then
        # backfill existing rows to keep ordering by tagged_at well-defined.
        conn.execute("ALTER TABLE article_tags ADD COLUMN tagged_at TEXT")
        conn.execute(
            "UPDATE article_tags SET tagged_at = datetime('now') "
            "WHERE tagged_at IS NULL"
        )
