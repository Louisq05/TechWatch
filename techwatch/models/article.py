"""Data access for feeds, articles and tags."""


def add_feed(conn, url, title=None):
    """Insert a feed, ignoring duplicates. Return its id."""
    conn.execute(
        "INSERT OR IGNORE INTO feeds (url, title) VALUES (?, ?)", (url, title)
    )
    conn.commit()
    row = conn.execute("SELECT id FROM feeds WHERE url = ?", (url,)).fetchone()
    return row["id"]


def get_feeds(conn):
    return conn.execute("SELECT * FROM feeds ORDER BY title").fetchall()


def add_article(conn, feed_id, title, link, summary=None, published=None):
    """Insert an article. Return id, or None if the link already exists."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO articles (feed_id, title, link, summary, published) "
        "VALUES (?, ?, ?, ?, ?)",
        (feed_id, title, link, summary, published),
    )
    conn.commit()
    return cur.lastrowid if cur.rowcount else None


def list_articles(conn, unread_only=False, tag=None):
    sql = "SELECT a.* FROM articles a JOIN feeds f ON f.id = a.feed_id "
    params, where = [], []
    # Default view: newest first by publication date; articles without one fall
    # back to when they were fetched. NULL published sorts last under DESC.
    order = "a.published DESC, a.fetched_at DESC"
    if tag is not None:
        sql += (
            "JOIN article_tags at ON at.article_id = a.id "
            "JOIN tags t ON t.id = at.tag_id "
        )
        where.append("t.name = ?")
        params.append(tag)
        # Tag view: most recently tagged first (rowid breaks within-second ties).
        order = "at.tagged_at DESC, at.rowid DESC"
    if unread_only:
        where.append("a.is_read = 0")
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY " + order
    return conn.execute(sql, params).fetchall()


def save_view(conn, article_ids):
    """Remember the order of the last listing so display numbers (1-based) can
    be mapped back to article ids by read/tag commands."""
    conn.execute("DELETE FROM last_view")
    conn.executemany(
        "INSERT INTO last_view (pos, article_id) VALUES (?, ?)",
        list(enumerate(article_ids, start=1)),
    )
    conn.commit()


def resolve_view(conn, pos):
    """Return the article id shown at display number `pos`, or None if the
    number is out of range (or no listing has been displayed yet)."""
    row = conn.execute(
        "SELECT article_id FROM last_view WHERE pos = ?", (pos,)
    ).fetchone()
    return row["article_id"] if row else None


def articles_since(conn, since):
    """Articles fetched strictly after the SQLite timestamp `since`, newest
    first. Used to build a digest of what arrived since the last one."""
    return conn.execute(
        "SELECT a.* FROM articles a WHERE a.fetched_at > ? "
        "ORDER BY a.published DESC, a.fetched_at DESC",
        (since,),
    ).fetchall()


def get_meta(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def touch_meta_now(conn, key):
    """Store the current SQLite time under `key` (same clock as fetched_at)."""
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value = datetime('now')",
        (key,),
    )
    conn.commit()


def mark_read(conn, article_id):
    conn.execute("UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,))
    conn.commit()


def add_tag(conn, article_id, tag_name):
    """Tag an article, creating the tag if needed."""
    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
    tag_id = conn.execute(
        "SELECT id FROM tags WHERE name = ?", (tag_name,)
    ).fetchone()["id"]
    # Record when the tag was applied so tag listings can order by recency.
    conn.execute(
        "INSERT OR IGNORE INTO article_tags (article_id, tag_id, tagged_at) "
        "VALUES (?, ?, datetime('now'))",
        (article_id, tag_id),
    )
    conn.commit()
