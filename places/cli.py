import argparse


def main():
    # Set up the parser
    parser = argparse.ArgumentParser(description="Semantic Search on your Browser History.")
    subparsers = parser.add_subparsers(help='sub-command help')

    index_parser = subparsers.add_parser("index", help="Index your browser history")
    index_parser.add_argument("database")
    index_parser.set_defaults(func=main)

    query_parser = subparsers.add_parser("query", help="Query your browser history")
    query_parser.add_argument("query")
    query_parser.set_defaults(func=run_query)

    web_parser = subparsers.add_parser("web", help="Run the web server")
    web_parser.set_defaults(func=run_web)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def run_index(args):
    from places.index import main

    main(args.database)


def run_query(args):
    from places.query import query

    query(args.query)


def run_web(args):
    from places.web import run

    run(host="0.0.0.0", port=8080)
