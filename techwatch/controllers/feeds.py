"""Fetch and normalise RSS/Atom feeds."""
import time

import feedparser


def _to_iso(struct_time):
    """Format a feedparser time.struct_time (UTC) as a sortable ISO 8601 string."""
    if not struct_time:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", struct_time)


def fetch_feed(url):
    """Return (title, entries) where entries is a list of normalised dicts."""
    parsed = feedparser.parse(url)
    title = parsed.feed.get("title") if parsed.feed else None
    entries = [
        {
            "title": e.get("title", "(sans titre)"),
            "link": e.get("link"),
            "summary": e.get("summary"),
            # Stored as ISO 8601 (UTC) so it sorts lexicographically; None if
            # the feed gives no parseable date.
            "published": _to_iso(e.get("published_parsed")),
        }
        for e in parsed.entries
        if e.get("link")
    ]
    return title, entries
