"""High-level operations wiring feeds, storage and views together."""
from ..models import article as repo
from .feeds import fetch_feed


def add_feed(conn, url):
    """Fetch the feed once to grab its title, then store it."""
    title, _ = fetch_feed(url)
    return repo.add_feed(conn, url, title)


def refresh(conn):
    """Fetch every feed and store new articles. Return count added."""
    added = 0
    for feed in repo.get_feeds(conn):
        _, entries = fetch_feed(feed["url"])
        for e in entries:
            if repo.add_article(
                conn, feed["id"], e["title"], e["link"],
                e["summary"], e["published"],
            ):
                added += 1
    return added
