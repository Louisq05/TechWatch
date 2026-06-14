"""Compose and send the e-mail digest of newly fetched articles."""
import logging

from ..models import article as repo
from ..views import email
from . import mailer

_LAST = "last_digest_at"


def send_digest(conn):
    """E-mail the articles fetched since the last digest. Return how many were
    sent, or 0 if there was nothing new."""
    since = repo.get_meta(conn, _LAST) or "1970-01-01 00:00:00"
    rows = repo.articles_since(conn, since)
    if not rows:
        logging.info("digest : rien de neuf, pas d'envoi")
        return 0
    subject, text_body, html_body = email.format_digest(rows)
    mailer.send(subject, text_body, html_body)
    repo.touch_meta_now(conn, _LAST)  # only advance after a successful send
    logging.info("digest : %d article(s) envoyé(s)", len(rows))
    return len(rows)
