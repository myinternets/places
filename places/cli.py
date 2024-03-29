import argparse
import asyncio
import logging
import sys


def set_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


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

    load_parser = subparsers.add_parser("load", help="Load models")
    load_parser.set_defaults(func=load_models)

    web_parser = subparsers.add_parser("web", help="Run the web server")
    web_parser.set_defaults(func=run_web)
    web_parser.add_argument(
        "--db", type=str, default="qdrant", choices=["qdrant", "vectra"]
    )
    web_parser.add_argument("--vectra-path", type=str, default="data.db")
    web_parser.add_argument("--qdrant-host", type=str, default="localhost")
    web_parser.add_argument("--qdrant-port", type=int, default=6333)
    args = parser.parse_args()

    set_logger()

    if hasattr(args, "func"):
        args = vars(args)
        func = args.pop("func")
        func(args)
    else:
        parser.print_help()


def run_index(args):
    from places.index.main import main

    asyncio.run(main(args["database"]))


def run_query(args):
    from places.query import query

    query(args["query"])


def load_models(args):
    import nltk

    nltk.download("bcp47")
    nltk.download("punkt")

    from places import vectors  # NOQA

    print("LOADED!")


def run_web(args):
    load_models(args)

    from places.web import main

    main(args)
