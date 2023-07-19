"""
Web app
"""
import logging
import os
from collections import OrderedDict
from uuid import uuid4

from aiohttp import web

from places.apis import apis
from places.app import PlacesApplication
from places.utils import build_answer

HERE = os.path.dirname(__file__)
STATIC = os.path.join(HERE, "static")
routes = web.RouteTableDef()

ANSWERS = {}


@routes.get("/search")
async def search(request):
    q = request.query["q"].strip()
    question = q.endswith("?")

    res = OrderedDict()

    urls = []

    print("Querying..")

    for hit in await request.app.query(q):
        url = hit["url"]
        title = hit["title"]
        key = url, title
        sentence = hit["sentence"]
        if url not in urls:
            urls.append(url)

        if key in res:
            if sentence not in res[key]:
                res[key].append(sentence)
        else:
            res[key] = [sentence]

    hits = [list(k) + [sentences] for k, sentences in res.items()]

    if question and len(urls) > 0:
        uuid = str(uuid4())
        url = urls[0]
        text = request.app.pages_db.get(url)["text"]

        # keep only the last ten entries
        if len(ANSWERS) > 10:
            oldest_key = next(iter(ANSWERS))
            del ANSWERS[oldest_key]

        ANSWERS[uuid] = request.app.task_executor(build_answer, url, q, text)
        print(f"answer id {uuid}")
    else:
        uuid = None

    args = {
        "hits": hits,
        "query": q,
        "answer_uuid": uuid,
    }
    return await request.app.html_resp("index.html", **args)


@routes.get("/admin")
async def admin(request):
    indexed = []
    async for domain in request.app.db.get_indexed_domains():
        indexed.append(domain)

    skipped = []
    async for domain in request.app.db.get_skipped_domains():
        skipped.append(domain)

    args = {
        "indexed": indexed,
        "skipped": skipped,
    }

    return await request.app.html_resp("admin.html", **args)


@routes.get("/")
async def index(request):
    return await request.app.html_resp("index.html")


def main(args):
    logging.getLogger("asyncio").setLevel(logging.DEBUG)
    app = PlacesApplication(args)
    app.add_routes(routes)
    app.add_routes(apis)
    app.add_routes([web.static("/static", STATIC)])
    app.init_db()
    print("Starting semantic bookmarks server...")
    web.run_app(app, port=8080)
