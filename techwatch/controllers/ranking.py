"""Score and rank articles by relevance, driven by ranking.toml (user-editable).

score(row, config) -> (score, reasons). rank(rows, config) -> sorted list.
"""
import re
import tomllib
import unicodedata
from datetime import datetime, timezone

from ..models.db import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "ranking.toml"


def load_config(path=CONFIG_PATH):
    with open(path, "rb") as f:
        return tomllib.load(f)


def _normalize(text):
    """Lowercase and strip accents so 'modèle' matches 'modele', etc."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _matches(word, text):
    """Whole-word, accent-insensitive search (avoids 'ai' matching 'rain')."""
    return re.search(rf"\b{re.escape(_normalize(word))}\b", text) is not None


def _freshness(published, cfg):
    if not published:
        return 0.0
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    jours = cfg.get("jours", 7)
    if age < 0 or age >= jours:
        return 0.0
    return cfg["poids"] * (1 - age / jours)


def _has(row, key):
    try:
        return key in row.keys()      # sqlite3.Row
    except AttributeError:
        return key in row             # plain dict


def score(row, config):
    """Return (total, reasons) for one article row."""
    # Match on the title only: it is a dense, clean signal. Summaries are long
    # and noisy (newsletters etc.) and produce many false theme matches.
    text = _normalize(row["title"])
    total = 0.0
    reasons = []

    for theme in config.get("theme", []):
        if any(_matches(m, text) for m in theme["mots"]):
            total += theme["poids"]
            reasons.append(theme["nom"])

    sources = config.get("sources", {})
    feed = row["feed_title"] if _has(row, "feed_title") else None
    if feed and feed in sources:
        total += sources[feed]
        reasons.append(f"source:{feed}")

    fresh = config.get("fraicheur")
    if fresh:
        bonus = _freshness(row["published"] if _has(row, "published") else None, fresh)
        if bonus:
            total += bonus
            reasons.append("récent")

    return round(total, 2), reasons


def rank(rows, config):
    """Return rows as (score, reasons, row), best first."""
    scored = [(*score(r, config), r) for r in rows]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
