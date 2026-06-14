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
    """Create tables from schema.sql if they do not exist yet."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
