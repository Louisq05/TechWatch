"""Automated pipeline run by the scheduler.

For now it just fetches new articles. This is the extension point where the
ranking step (2) and the e-mail digest (3) will be plugged in later.

Run manually with:  python -m techwatch.pipeline
"""
import logging

from .models import db
from .controllers import library
from .controllers import digest

LOG_PATH = db.PROJECT_ROOT / "techwatch.log"


def run():
    """Fetch new articles, then e-mail a digest. Return (added, sent)."""
    conn = db.connect()
    db.init_db(conn)
    added = library.refresh(conn)
    logging.info("refresh terminé : %d nouvel(s) article(s)", added)
    try:
        sent = digest.send_digest(conn)
    except Exception:
        # A mail failure (e.g. SMTP not configured yet) must not lose the
        # successful refresh above.
        logging.exception("digest : envoi impossible")
        sent = 0
    conn.close()
    return added, sent


def main():
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        encoding="utf-8",
    )
    try:
        run()
    except Exception:
        logging.exception("le pipeline a échoué")
        raise


if __name__ == "__main__":
    main()
