"""Render articles for the terminal."""


def format_articles(rows):
    if not rows:
        return "Aucun article."
    lines = []
    for r in rows:
        flag = " " if r["is_read"] else "*"
        lines.append(f"[{flag}] #{r['id']:>4}  {r['title']}")
        lines.append(f"          {r['link']}")
    return "\n".join(lines)
