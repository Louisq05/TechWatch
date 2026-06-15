"""techwatch — CLI entry point."""
import argparse
import sys

from techwatch.models import db
from techwatch.models import article as repo
from techwatch.controllers import library
from techwatch.views import console


def main(argv=None):
    # Feed content is arbitrary Unicode; Windows consoles default to cp1252,
    # which crashes on characters like → or em dashes. Force UTF-8 output.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="techwatch", description="Veille tech RSS.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-feed", help="Ajouter un flux RSS")
    p.add_argument("url")

    sub.add_parser("import-feeds", help="Ajouter les flux listés dans feeds.txt")

    sub.add_parser("refresh", help="Récupérer les nouveaux articles")

    p = sub.add_parser("list", help="Lister les articles")
    p.add_argument("--unread", action="store_true")
    p.add_argument("--tag")

    p = sub.add_parser("read", help="Marquer un article comme lu")
    p.add_argument("num", type=int, help="numéro affiché dans la dernière liste")

    p = sub.add_parser("tag", help="Taguer un article")
    p.add_argument("num", type=int, help="numéro affiché dans la dernière liste")
    p.add_argument("tag")

    args = parser.parse_args(argv)
    conn = db.connect()
    db.init_db(conn)

    if args.cmd == "add-feed":
        feed_id = library.add_feed(conn, args.url)
        print(f"Flux ajouté (#{feed_id}).")
    elif args.cmd == "import-feeds":
        lines = (db.PROJECT_ROOT / "feeds.txt").read_text(encoding="utf-8").splitlines()
        urls = [s for s in (ln.strip() for ln in lines) if s and not s.startswith("#")]
        for url in urls:
            library.add_feed(conn, url)
        print(f"{len(urls)} flux importés depuis feeds.txt.")
    elif args.cmd == "refresh":
        print(f"{library.refresh(conn)} nouvel(s) article(s).")
    elif args.cmd == "list":
        rows = repo.list_articles(conn, unread_only=args.unread, tag=args.tag)
        repo.save_view(conn, [r["id"] for r in rows])
        print(console.format_articles(rows))
    elif args.cmd == "read":
        article_id = repo.resolve_view(conn, args.num)
        if article_id is None:
            print(f"Numéro {args.num} introuvable. Lance d'abord « list ».")
        else:
            repo.mark_read(conn, article_id)
            print(f"Article n°{args.num} marqué comme lu.")
    elif args.cmd == "tag":
        article_id = repo.resolve_view(conn, args.num)
        if article_id is None:
            print(f"Numéro {args.num} introuvable. Lance d'abord « list ».")
        else:
            repo.add_tag(conn, article_id, args.tag)
            print(f"Article n°{args.num} tagué « {args.tag} ».")


if __name__ == "__main__":
    main()
