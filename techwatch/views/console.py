"""Render articles for the terminal."""


def format_articles(rows):
    """Render rows with a 1-based display number (position in this listing),
    not the internal article id. Number 1 is the top (most recent) row."""
    if not rows:
        return "Aucun article."
    lines = []
    for pos, r in enumerate(rows, start=1):
        flag = " " if r["is_read"] else "*"
        lines.append(f"[{flag}] #{pos:>3}  {r['title']}")
        lines.append(f"          {r['link']}")
    return "\n".join(lines)
