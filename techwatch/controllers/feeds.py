"""Fetch and normalise RSS/Atom feeds."""
import feedparser


def fetch_feed(url):
    """Return (title, entries) where entries is a list of normalised dicts."""
    parsed = feedparser.parse(url)
    title = parsed.feed.get("title") if parsed.feed else None
    entries = [
        {
            "title": e.get("title", "(sans titre)"),
            "link": e.get("link"),
            "summary": e.get("summary"),
            "published": e.get("published"),
        }
        for e in parsed.entries
        if e.get("link")
    ]
    return title, entries
