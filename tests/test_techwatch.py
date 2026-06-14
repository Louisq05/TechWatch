"""Tests for the data layer (no network)."""
from techwatch.models import article as repo


def test_schema_creates_tables(conn):
    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {"feeds", "articles", "tags", "article_tags"} <= tables


def test_add_feed_is_idempotent(conn):
    first = repo.add_feed(conn, "https://ex.com/feed", "Example")
    second = repo.add_feed(conn, "https://ex.com/feed", "Example")
    assert first == second
    assert len(repo.get_feeds(conn)) == 1


def test_add_article_dedupes_on_link(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    a = repo.add_article(conn, feed_id, "Hello", "https://ex.com/1")
    dup = repo.add_article(conn, feed_id, "Hello again", "https://ex.com/1")
    assert a is not None
    assert dup is None
    assert len(repo.list_articles(conn)) == 1


def test_mark_read(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    art = repo.add_article(conn, feed_id, "T", "https://ex.com/2")
    assert len(repo.list_articles(conn, unread_only=True)) == 1
    repo.mark_read(conn, art)
    assert len(repo.list_articles(conn, unread_only=True)) == 0


def test_list_orders_by_published_desc(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    repo.add_article(conn, feed_id, "Vieux", "https://ex.com/old",
                     published="2020-01-01T00:00:00Z")
    repo.add_article(conn, feed_id, "Recent", "https://ex.com/new",
                     published="2026-01-01T00:00:00Z")
    titles = [r["title"] for r in repo.list_articles(conn)]
    assert titles == ["Recent", "Vieux"]


def test_tagging_and_filter(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    art = repo.add_article(conn, feed_id, "AI piece", "https://ex.com/3")
    repo.add_tag(conn, art, "ia")
    assert len(repo.list_articles(conn, tag="ia")) == 1
    assert len(repo.list_articles(conn, tag="autre")) == 0
