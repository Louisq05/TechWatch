-- techwatch schema (SQLite)

CREATE TABLE IF NOT EXISTS feeds (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    url      TEXT NOT NULL UNIQUE,
    title    TEXT,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id    INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    link       TEXT NOT NULL UNIQUE,
    summary    TEXT,
    published  TEXT,
    is_read    INTEGER NOT NULL DEFAULT 0,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id     INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    tagged_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (article_id, tag_id)
);

-- Ephemeral cache: maps the display numbers (1..N) of the last `list` output
-- to article ids, so `read N` / `tag N` resolve the number the user just saw.
CREATE TABLE IF NOT EXISTS last_view (
    pos        INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE
);

-- Small key/value store for app state (e.g. when the last digest was sent).
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
