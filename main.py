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

    sub.add_parser("refresh", help="Récupérer les nouveaux articles")

    p = sub.add_parser("list", help="Lister les articles")
    p.add_argument("--unread", action="store_true")
    p.add_argument("--tag")

    p = sub.add_parser("read", help="Marquer un article comme lu")
    p.add_argument("article_id", type=int)

    p = sub.add_parser("tag", help="Taguer un article")
    p.add_argument("article_id", type=int)
    p.add_argument("tag")

    args = parser.parse_args(argv)
    conn = db.connect()
    db.init_db(conn)

    if args.cmd == "add-feed":
        feed_id = library.add_feed(conn, args.url)
        print(f"Flux ajouté (#{feed_id}).")
    elif args.cmd == "refresh":
        print(f"{library.refresh(conn)} nouvel(s) article(s).")
    elif args.cmd == "list":
        rows = repo.list_articles(conn, unread_only=args.unread, tag=args.tag)
        print(console.format_articles(rows))
    elif args.cmd == "read":
        repo.mark_read(conn, args.article_id)
        print(f"Article #{args.article_id} marqué comme lu.")
    elif args.cmd == "tag":
        repo.add_tag(conn, args.article_id, args.tag)
        print(f"Article #{args.article_id} tagué « {args.tag} ».")


if __name__ == "__main__":
    main()
