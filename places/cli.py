import argparse
import asyncio


def main():
    # Set up the parser
    parser = argparse.ArgumentParser(
        description="Semantic Search on your Browser History."
    )
    subparsers = parser.add_subparsers(help="sub-command help")

    index_parser = subparsers.add_parser("index", help="Index your browser history")
    index_parser.add_argument("database")
    index_parser.set_defaults(func=run_index)

    query_parser = subparsers.add_parser("query", help="Query your browser history")
    query_parser.add_argument("query")
    query_parser.set_defaults(func=run_query)

    web_parser = subparsers.add_parser("web", help="Run the web server")
    web_parser.set_defaults(func=run_web)
    web_parser.add_argument(
        "--db", type=str, default="qdrant", choices=["qdrant", "vectra"]
    )
    web_parser.add_argument("--vectra-path", type=str, default="data.db")
    web_parser.add_argument("--qdrant-host", type=str, default="localhost")
    web_parser.add_argument("--qdrant-port", type=int, default=6333)
    args = parser.parse_args()

    if hasattr(args, "func"):
        args = vars(args)
        func = args.pop("func")
        func(args)
    else:
        parser.print_help()


def run_index(args):
    from places.index import main

    asyncio.run(main(args.database))


def run_query(args):
    from places.query import query

    query(args.query)


def run_web(args):
    from places.web import main

    main(args)
