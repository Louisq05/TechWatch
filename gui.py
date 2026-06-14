"""techwatch — graphical interface entry point (run: python gui.py)."""
from techwatch.models import db
from techwatch.views import gui


def main():
    conn = db.connect()
    db.init_db(conn)
    gui.run(conn)


if __name__ == "__main__":
    main()
