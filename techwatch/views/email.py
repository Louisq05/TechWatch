"""Render a digest of articles as an e-mail (plain text + HTML)."""
from datetime import date
from html import escape


def format_digest(rows):
    """Return (subject, text_body, html_body) for the given article rows."""
    n = len(rows)
    subject = f"techwatch — {n} nouvel(s) article(s) ({date.today():%d/%m/%Y})"

    text_lines = [f"{n} nouvel(s) article(s) :", ""]
    for r in rows:
        text_lines.append(f"- {r['title']}")
        text_lines.append(f"  {r['link']}")
    text_body = "\n".join(text_lines)

    items = "\n".join(
        '<li style="margin-bottom:12px">'
        f'<a href="{escape(r["link"])}" '
        'style="color:#5865f2;text-decoration:none;font-weight:600">'
        f'{escape(r["title"])}</a></li>'
        for r in rows
    )
    html_body = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:640px;'
        'color:#1e1f22">'
        f'<h2>techwatch — {n} nouvel(s) article(s)</h2>'
        f'<ul style="list-style:none;padding:0">{items}</ul>'
        '</div>'
    )
    return subject, text_body, html_body
