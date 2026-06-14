"""Compose and send the e-mail digest of newly fetched articles."""
import logging

from ..models import article as repo
from ..views import email
from . import mailer, ranking

_LAST = "last_digest_at"


def send_digest(conn, config=None):
    """E-mail the most relevant articles fetched since the last digest, ranked
    by score. Return how many were sent, or 0 if there was nothing new."""
    since = repo.get_meta(conn, _LAST) or "1970-01-01 00:00:00"
    rows = repo.articles_since(conn, since)
    if not rows:
        logging.info("digest : rien de neuf, pas d'envoi")
        return 0
    if config is None:
        config = ranking.load_config()
    ranked = ranking.rank(rows, config)
    max_n = config.get("digest", {}).get("max", 15)
    # Keep the relevant ones (positive score); never mail what was penalised.
    selected = [item for item in ranked if item[0] > 0][:max_n]
    if not selected:  # nothing scored positively -> fall back to the top few
        selected = ranked[:max_n]
    subject, text_body, html_body = email.format_digest(selected)
    mailer.send(subject, text_body, html_body)
    repo.touch_meta_now(conn, _LAST)  # only advance after a successful send
    logging.info("digest : %d/%d article(s) envoyé(s)", len(selected), len(rows))
    return len(selected)
