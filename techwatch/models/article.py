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
    if tag is not None:
        sql += (
            "JOIN article_tags at ON at.article_id = a.id "
            "JOIN tags t ON t.id = at.tag_id "
        )
        where.append("t.name = ?")
        params.append(tag)
    if unread_only:
        where.append("a.is_read = 0")
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    # Newest first by publication date; articles without one fall back to
    # when they were fetched. NULL published sorts last under DESC in SQLite.
    sql += "ORDER BY a.published DESC, a.fetched_at DESC"
    return conn.execute(sql, params).fetchall()


def mark_read(conn, article_id):
    conn.execute("UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,))
    conn.commit()


def add_tag(conn, article_id, tag_name):
    """Tag an article, creating the tag if needed."""
    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
    tag_id = conn.execute(
        "SELECT id FROM tags WHERE name = ?", (tag_name,)
    ).fetchone()["id"]
    conn.execute(
        "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
        (article_id, tag_id),
    )
    conn.commit()
