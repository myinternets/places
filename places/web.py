import asyncio
import json
import logging
import os
import traceback as tb
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor

import numpy
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from places.backends import get_db
from places.utils import answer
from places.vectors import build_vector, model
from places.db import Pages, DB


HERE = os.path.dirname(__file__)
routes = web.RouteTableDef()
STATIC = os.path.join(HERE, "static")


def error_to_json(e):
    return {
        "error": repr(e),
        "tb": "".join(tb.format_exception(None, e, e.__traceback__)),
    }


@routes.post("/index")
async def index_doc(request):
    try:
        data = await request.json()
        url = data["url"]
        if await request.app.db.get_skip(url):
            print(f"Skipping {url}")
            return await request.app.json_resp({"result": "skipped domain"}, 200)

        # storing the page
        request.app.pages_db.set(url, {"html": data["text"]})
        v_payload = json.dumps({"url": url, "text": data["text"]})

        try:
            resp = await request.app.run_in_executor(build_vector, v_payload)
        except Exception as e:
            print(f"Failed to vectorize {repr(e)}")
            return await request.app.json_resp({"error": str(e)}, 400)

        resp = json.loads(resp)

        if "error" in resp:
            print(f"Failed to vectorize {resp['error']}")
            return await request.app.json_resp(resp, 400)

        vectors = resp["vectors"]
        sentences = resp["sentences"]
        title = resp["title"]

        if len(sentences) < 5:
            print(f"only {len(sentences)} skipping")
            return await request.app.json_resp(
                {"result": f"only {len(sentences)} skipping"}, 200
            )

        points = []

        for idx, (vec, sentence) in enumerate(zip(vectors, sentences, strict=True)):
            try:
                point = request.app.client.create_point(
                    idx, url, title, list(numpy.asfarray(vec)), sentence
                )
            except Exception as e:
                print("Failed to create a point")
                return await request.app.json_resp({"error": str(e)}, 400)

            points.append(point)

        try:
            resp = await request.app.client.index(points=points)
            resp = [json.loads(item) for item in resp]
            resp = {
                "backend_resp": resp,
                "message": f"Vectorized {len(sentences)} sentences",
            }
            res = await request.app.json_resp(resp)
        except Exception as e:
            print("Failed to send points to vector db")
            return await request.app.json_resp({"error": str(e)}, 400)

        await request.app.db.indexed(url)
        return res

    except Exception as e:
        return await request.app.json_resp(error_to_json(e), 400)


@routes.get("/search")
async def search(request):
    q = request.query["q"].strip()
    question = q.endswith("?")

    res = OrderedDict()

    urls = []

    print("Queyring..")
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

    # answers could be built asynchronously and update the page after
    # it's expensive!
    answers = []

    if question:
        # XXX building just the first one
        for url in urls[:1]:
            print(f"Building answer for {url}")
            text = request.app.pages_db.get(url)["text"]
            a = answer(q, text)

            # XXX UGLY
            # grabbing the surroundings of the answer
            n_start = a["start"]
            n_end = a["end"]
            while text[n_start] != "\n" and n_start > 0:
                n_start -= 1
            while text[n_end] != "\n" and n_end < len(text):
                n_end += 1
            extract = text[n_start:n_end]
            extract = extract.replace(
                a["answer"], f'<span class="answer">{a["answer"]}</span>'
            )

            answers.append(
                {
                    "answer": a["answer"],
                    "url": url,
                    "score": a["score"],
                    "extract": extract,
                }
            )

        answers.sort(reverse=True)

    args = {
        "args": {"title": "My Internets"},
        "description": "Search Your History",
        "hits": hits,
        "answers": answers,
        "query": q,
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
        "args": {"title": "My Internets"},
        "description": "Search Your History",
        "answers": [],
        "indexed": indexed,
        "skipped": skipped,
    }

    return await request.app.html_resp("admin.html", **args)


@routes.get("/remove_index")
async def remove_index(request):
    domain = request.rel_url.query["domain"]
    await request.app.db.set_skip(domain, True)
    # TODO: remove indexed content...
    raise web.HTTPFound("/admin")


@routes.get("/remove_skip")
async def remove_skip(request):
    domain = request.rel_url.query["domain"]
    await request.app.db.set_skip(domain, False)
    raise web.HTTPFound("/admin")


@routes.get("/domain_info")
async def info(request):
    url = request.rel_url.query["url"]
    res = await request.app.db.domain_info(url)
    return web.json_response(res)


@routes.get("/")
async def index(request):
    args = {
        "args": {"title": "My Internets"},
        "description": "Search Your History",
        "answers": [],
    }
    return await request.app.html_resp("index.html", **args)


class PlacesApplication(web.Application):
    def __init__(self, args):
        super().__init__(client_max_size=None)
        self.env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")))
        self.client = get_db(**args)
        self.executor = ProcessPoolExecutor()
        self.on_startup.append(self._startup)
        self.on_cleanup.append(self._cleanup)
        self.pages_db = Pages("/tmp/pages")
        self.db = DB()

    async def _startup(self, app):
        self["loop"] = asyncio.get_running_loop()
        await self.db.check_db()

    async def _cleanup(self, app):
        self.executor.shutdown()

    async def query(self, sentence):
        # vectorize the query
        embedding = await self.run_in_executor(model.encode, [sentence])
        vector = numpy.asfarray(embedding[0])
        vector = list(vector)
        hits = []
        async for hit in self.client.search(query_vector=vector, limit=10):
            hits.append(hit)
        return hits

    def init_db(self):
        self.client.init_db()

    async def get_db_info(self):
        return await self.client.get_db_info()

    async def html_resp(self, template, status=200, **args):
        template = self.env.get_template(template)
        args["db_info"] = await self.get_db_info()
        content = template.render(**args)
        resp = web.Response(text=content)
        resp.headers["Content-Type"] = "text/html"
        resp.set_status(status)
        return resp

    async def json_resp(self, body, status=200):
        if not isinstance(body, str):
            body = json.dumps(body)
        resp = web.Response(text=body)
        resp.headers["Content-Type"] = "application/json"
        resp.set_status(status)
        return resp

    async def run_in_executor(self, function, *args, **kw):
        task = self["loop"].run_in_executor(self.executor, function, *args, **kw)
        await task

        if task.exception() is not None:
            raise task.exception()

        return task.result()


def main(args):
    logging.getLogger("asyncio").setLevel(logging.DEBUG)
    app = PlacesApplication(args)
    app.add_routes(routes)
    app.add_routes([web.static("/static", STATIC)])
    app.init_db()
    print("Starting semantic bookmarks server...")
    web.run_app(app, port=8080)
