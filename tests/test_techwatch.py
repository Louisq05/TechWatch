"""Tests for the data layer (no network)."""
from techwatch.models import article as repo
from techwatch.views import email as email_view
from techwatch.controllers import digest, mailer, ranking


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


def test_tag_list_ordered_by_tagging_recency(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    a1 = repo.add_article(conn, feed_id, "Premier", "https://ex.com/1")
    a2 = repo.add_article(conn, feed_id, "Second", "https://ex.com/2")
    repo.add_tag(conn, a1, "x")
    repo.add_tag(conn, a2, "x")  # tagué après a1 -> doit apparaître en premier
    titles = [r["title"] for r in repo.list_articles(conn, tag="x")]
    assert titles == ["Second", "Premier"]


def test_view_maps_display_number_to_article(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    recent = repo.add_article(conn, feed_id, "Recent", "https://ex.com/r",
                              published="2026-01-02T00:00:00Z")
    old = repo.add_article(conn, feed_id, "Vieux", "https://ex.com/o",
                           published="2026-01-01T00:00:00Z")
    rows = repo.list_articles(conn)
    repo.save_view(conn, [r["id"] for r in rows])
    # Plus récent en haut -> numéro 1 ; les numéros croissent vers le bas.
    assert repo.resolve_view(conn, 1) == recent
    assert repo.resolve_view(conn, 2) == old
    assert repo.resolve_view(conn, 99) is None


def test_articles_since(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    repo.add_article(conn, feed_id, "A", "https://ex.com/a")
    assert len(repo.articles_since(conn, "1970-01-01 00:00:00")) == 1
    assert len(repo.articles_since(conn, "2999-01-01 00:00:00")) == 0


def test_meta_roundtrip(conn):
    assert repo.get_meta(conn, "k") is None
    repo.touch_meta_now(conn, "k")
    assert repo.get_meta(conn, "k") is not None


def test_format_digest_lists_links_and_escapes(conn):
    feed_id = repo.add_feed(conn, "https://ex.com/feed", "Ma Source")
    repo.add_article(conn, feed_id, "Hello <b>", "https://ex.com/x",
                     author="Jane Doe")
    rows = repo.articles_since(conn, "1970-01-01 00:00:00")
    items = [(5.0, ["IA"], r) for r in rows]
    subject, text, html = email_view.format_digest(items)
    assert "1" in subject
    assert "https://ex.com/x" in text
    assert "&lt;b&gt;" in html         # titles are HTML-escaped
    assert "Ma Source" in html         # source shown
    assert "Jane Doe" in html          # author shown when present


def test_send_digest_ranks_filters_and_marks(conn, monkeypatch):
    feed_id = repo.add_feed(conn, "https://ex.com/feed")
    repo.add_article(conn, feed_id, "Big AI news", "https://ex.com/a")
    repo.add_article(conn, feed_id, "Boring linux kernel changelog", "https://ex.com/b")
    captured = {}
    monkeypatch.setattr(
        mailer, "send",
        lambda subject, text, html: captured.update(text=text) or "to@x",
    )
    cfg = {
        "theme": [
            {"nom": "IA", "poids": 3.0, "mots": ["ai"]},
            {"nom": "Niche", "poids": -2.0, "mots": ["linux", "kernel"]},
        ],
        "digest": {"max": 15},
    }
    # Only the AI article scores positively; the niche one is filtered out.
    assert digest.send_digest(conn, cfg) == 1
    assert "Big AI news" in captured["text"]
    assert "linux" not in captured["text"].lower()
    assert digest.send_digest(conn, cfg) == 0     # marker advanced -> nothing new


_RANK_CFG = {
    "theme": [
        {"nom": "IA", "poids": 3.0, "mots": ["ai", "claude"]},
        {"nom": "Niche", "poids": -2.0, "mots": ["linux", "kernel"]},
    ],
    "sources": {"MIT": 2.0},
}


def _row(title, feed_title="X"):
    return {"title": title, "summary": None, "published": None,
            "feed_title": feed_title}


def test_score_rewards_themes_and_penalises_niche():
    s_ai = ranking.score(_row("New Claude model is out"), _RANK_CFG)[0]
    s_niche = ranking.score(_row("Linux kernel 6.9 changelog"), _RANK_CFG)[0]
    s_neutral = ranking.score(_row("A story about cooking"), _RANK_CFG)[0]
    assert s_ai > s_neutral > s_niche


def test_score_word_boundaries_and_source_bonus():
    # "ai" must not match inside "rain"; source bonus applies by feed title.
    assert ranking.score(_row("Rain in Spain"), _RANK_CFG)[0] == 0.0
    assert ranking.score(_row("Plain news", feed_title="MIT"), _RANK_CFG)[0] == 2.0


def test_rank_orders_by_score():
    rows = [_row("cooking"), _row("Claude AI breakthrough"), _row("linux kernel")]
    ordered = ranking.rank(rows, _RANK_CFG)
    assert ordered[0][2]["title"] == "Claude AI breakthrough"
    assert ordered[-1][2]["title"] == "linux kernel"
