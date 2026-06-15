"""Render a digest of articles as an e-mail (plain text + HTML newsletter).

format_digest takes a list of (score, reasons, row) items — the output of
controllers.ranking.rank, already filtered/truncated by the digest.
"""
from datetime import date
from html import escape

# Theme -> (emoji, colour). Order here drives the order of sections.
THEME_STYLE = [
    ("IA", "🤖", "#5865f2"),
    ("Cyber", "🔒", "#e0533d"),
    ("Espace", "🚀", "#9b59b6"),
]
OTHER = ("Autre", "📰", "#6c7a89")

# Persistent footer pick: a "smart scroll" antidote to brainrot.
PICK_URL = "https://www.orangecrumbs.com/"
PICK_TITLE = "Pour soigner ton brainrot"
PICK_SUB = "Un scroll qui nourrit le cerveau, sur OrangeCrumbs."


def _has(row, key):
    try:
        return key in row.keys()      # sqlite3.Row
    except AttributeError:
        return key in row             # plain dict


def _field(row, key):
    return row[key] if _has(row, key) and row[key] else None


def _primary_theme(reasons):
    """Pick the section an item belongs to, by first matching positive theme."""
    for name, emoji, color in THEME_STYLE:
        if name in reasons:
            return name, emoji, color
    return OTHER


def _stars(score):
    """Map a score to a 1..5 star relevance badge."""
    n = (5 if score >= 6 else 4 if score >= 4.5 else 3 if score >= 3
         else 2 if score >= 1.5 else 1)
    return "★" * n + "☆" * (5 - n)


def _meta(row):
    """'Source · par Auteur' (auteur optionnel)."""
    parts = []
    if _field(row, "feed_title"):
        parts.append(row["feed_title"])
    if _field(row, "author"):
        parts.append(f"par {row['author']}")
    return " · ".join(parts)


def _group(items):
    """Group items by primary theme, themes first then Autre."""
    sections = {}
    for score, reasons, row in items:
        sections.setdefault(_primary_theme(reasons), []).append((score, row))
    order = list(THEME_STYLE) + [OTHER]
    return [(key, sections[key]) for key in order if key in sections]


def _article_html(score, row):
    title, link = escape(row["title"]), escape(row["link"])
    meta = escape(_meta(row))
    img = _field(row, "image")
    img_cell = (
        f'<td width="96" valign="top"><img src="{escape(img)}" width="84" '
        f'style="border-radius:6px" alt=""></td>' if img else ""
    )
    return (
        '<table cellpadding="0" cellspacing="0" style="margin:12px 0;width:100%">'
        f'<tr>{img_cell}<td valign="top">'
        f'<a href="{link}" style="color:#1e1f22;text-decoration:none;'
        f'font-weight:600;font-size:15px">{title}</a><br>'
        f'<span style="color:#6c7a89;font-size:13px">{meta}</span> '
        f'<span style="color:#f1c40f;font-size:13px" title="pertinence">'
        f'{_stars(score)}</span>'
        "</td></tr></table>"
    )


def format_digest(items):
    """items: list of (score, reasons, row). Return (subject, text, html)."""
    n = len(items)
    today = date.today()
    subject = f"techwatch — {n} article(s) du jour ({today:%d/%m/%Y})"
    grouped = _group(items)

    # --- plain text ---
    tlines = [f"techwatch — {today:%d/%m/%Y} · {n} article(s)", ""]
    for (name, _emoji, _color), arts in grouped:
        tlines.append(f"== {name} ==")
        for score, row in arts:
            tlines.append(f"- {row['title']}  ({_meta(row)})  {_stars(score)}")
            tlines.append(f"  {row['link']}")
        tlines.append("")
    tlines += [f"— {PICK_TITLE} : {PICK_SUB}", f"  {PICK_URL}", ""]
    text_body = "\n".join(tlines)

    # --- HTML newsletter ---
    blocks = []
    for (name, emoji, color), arts in grouped:
        blocks.append(
            f'<h2 style="color:{color};border-bottom:2px solid {color};'
            f'padding-bottom:4px;margin:24px 0 8px;font-size:16px">'
            f"{emoji} {escape(name)}</h2>"
        )
        blocks += [_article_html(score, row) for score, row in arts]

    pick = (
        '<div style="margin-top:24px;background:#fff4e6;border:1px solid #ffd9a8;'
        'border-radius:8px;padding:14px 18px">'
        f'<a href="{escape(PICK_URL)}" style="color:#e67e22;text-decoration:none;'
        f'font-weight:700;font-size:15px">💊 {escape(PICK_TITLE)} →</a>'
        f'<div style="color:#6c7a89;font-size:13px;margin-top:4px">'
        f"{escape(PICK_SUB)}</div></div>"
    )

    html_body = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:680px;'
        'margin:auto;color:#1e1f22;padding:8px">'
        '<div style="background:#1e1f22;color:#fff;padding:14px 18px;'
        'border-radius:8px">'
        '<span style="font-size:20px;font-weight:700">techwatch</span>'
        f'<span style="float:right;color:#9aa0a6;font-size:13px">'
        f"{today:%d/%m/%Y} · {n} articles</span></div>"
        + "".join(blocks)
        + pick
        + '<div style="margin-top:24px;padding-top:12px;border-top:1px solid #ddd;'
        'color:#9aa0a6;font-size:12px">Généré par techwatch · '
        "curation automatique de tes sources</div></div>"
    )
    return subject, text_body, html_body
