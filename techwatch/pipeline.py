"""Automated pipeline run by the scheduler.

For now it just fetches new articles. This is the extension point where the
ranking step (2) and the e-mail digest (3) will be plugged in later.

Run manually with:  python -m techwatch.pipeline
"""
import logging

from .models import db
from .controllers import library

LOG_PATH = db.PROJECT_ROOT / "techwatch.log"


def run():
    """Fetch new articles from every feed. Return the number added."""
    conn = db.connect()
    db.init_db(conn)
    added = library.refresh(conn)
    logging.info("refresh terminé : %d nouvel(s) article(s)", added)
    conn.close()
    return added


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
