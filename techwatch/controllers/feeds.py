"""Fetch and normalise RSS/Atom feeds."""
import re
import time

import feedparser


def _to_iso(struct_time):
    """Format a feedparser time.struct_time (UTC) as a sortable ISO 8601 string."""
    if not struct_time:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", struct_time)


def _extract_image(entry):
    """Best-effort thumbnail URL from the many places feeds hide it."""
    for key in ("media_thumbnail", "media_content"):
        media = entry.get(key)
        if media and media[0].get("url"):
            return media[0]["url"]
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image"):
            return link.get("href")
    if entry.get("image", {}).get("href"):
        return entry["image"]["href"]
    m = re.search(r'<img[^>]+src="([^"]+)"', entry.get("summary", "") or "")
    return m.group(1) if m else None


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
            "author": e.get("author"),
            "image": _extract_image(e),
        }
        for e in parsed.entries
        if e.get("link")
    ]
    return title, entries
