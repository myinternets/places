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
from places.utils import should_skip
from places.vectors import build_vector, model

HERE = os.path.dirname(__file__)
COLLECTION_NAME = "pages"
routes = web.RouteTableDef()


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
        if should_skip(url):
            print(f"Skipping {url}")
            return await request.app.json_resp({"result": "skipped domain"}, 200)

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
            res = await request.app.json_resp(resp)
        except Exception as e:
            print("Failed to send points to vector db")
            return await request.app.json_resp({"error": str(e)}, 400)

        return res

    except Exception as e:
        return await request.app.json_resp(error_to_json(e), 400)


@routes.get("/search")
async def search(request):
    q = request.query["q"]
    res = OrderedDict()

    for hit in await request.app.query(q):
        url = hit["url"]
        title = hit["title"]
        key = url, title
        sentence = hit["sentence"]

        if key in res:
            if sentence not in res[key]:
                res[key].append(sentence)
        else:
            res[key] = [sentence]

    hits = [list(k) + [sentences] for k, sentences in res.items()]

    args = {
        "args": {"title": "My Internets"},
        "description": "Search Your History",
        "hits": hits,
        "query": q,
    }
    return await request.app.html_resp("index.html", **args)


@routes.get("/")
async def index(request):
    args = {"args": {"title": "My Internets"}, "description": "Search Your History"}
    return await request.app.html_resp("index.html", **args)


class PlacesApplication(web.Application):
    def __init__(self, args):
        super().__init__(client_max_size=None)
        self.env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")))
        self.client = get_db(**args)
        self.executor = ProcessPoolExecutor()
        self.on_startup.append(self._startup)
        self.on_cleanup.append(self._cleanup)

    async def _startup(self, app):
        self["loop"] = asyncio.get_running_loop()

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
    app.init_db()
    print("Starting semantic bookmarks server...")
    web.run_app(app, port=8080)
