import asyncio
import hashlib
import json
import logging
import os
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor

import numpy
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

from places.vectors import build_vector

HERE = os.path.dirname(__file__)
COLLECTION_NAME = "pages"
routes = web.RouteTableDef()


def create_point(index, url, title, vec, sentence):
    point_id = hashlib.md5(f"{url}-{index}".encode()).hexdigest()

    return PointStruct(
        id=point_id,
        vector=list(numpy.asfarray(vec)),
        payload={"url": url, "sentence": sentence, "title": title},
    )


@routes.post("/index")
async def index_doc(request):
    try:
        data = await request.json()
        url = data["url"]

        v_payload = json.dumps({"url": url, "text": data["text"]})

        try:
            vector = await request.app.run_in_executor(build_vector, v_payload)
        except Exception as e:
            print("Failed to vectorize")
            return await request.app.json_resp({"error": str(e)}, 400)

        vector = json.loads(vector)

        vectors = vector["vectors"]
        sentences = vector["sentences"]
        title = vector["title"]
        points = []

        for idx, (vec, sentence) in enumerate(zip(vectors, sentences, strict=True)):
            try:
                point = create_point(idx, url, title, vec, sentence)
            except Exception as e:
                print("Failed to create a point")
                return await request.app.json_resp({"error": str(e)}, 400)

            points.append(point)

        # TODO IO-bound, should be done in an async call (qdrant_python supports this)
        try:
            res = await request.app.json_resp(
                request.app.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points,
                ).json()
            )
        except Exception as e:
            print("Failed to send points to qdrant")
            return await request.app.json_resp({"error": str(e)}, 400)

        return res

    except Exception as e:
        return await request.app.json_resp({"error": str(e)}, 400)


@routes.get("/search")
async def search(request):
    q = request.query["q"]
    res = OrderedDict()

    for hit in await request.app.query(q):
        payload = hit.payload
        url = payload["url"]
        title = payload["title"]
        key = url, title
        sentence = payload["sentence"]

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
    def __init__(self, *args, **kw):
        self.qdrant_host = kw.pop("qdrant_host", "localhost")
        self.qdrant_port = kw.pop("qdrant_port", 6333)

        super().__init__(*args, **kw)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")))
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        self.executor = ProcessPoolExecutor()
        self.on_startup.append(self._startup)
        self.on_cleanup.append(self._cleanup)

    async def _startup(self, app):
        self["loop"] = asyncio.get_running_loop()

    async def _cleanup(self, app):
        self.executor.shutdown()

    async def query(self, sentence):
        # vectorize the query
        embedding = await self.run_in_executor(self.model.encode, [sentence])
        vector = numpy.asfarray(embedding[0])
        vector = list(vector)
        # should move to i-o bound
        hits = self.client.search(
            collection_name=COLLECTION_NAME, query_vector=vector, limit=10
        )
        return hits

    def init_db(self):
        try:
            self.client.get_collection(collection_name=COLLECTION_NAME)
            return
        except Exception:
            self.client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=384, distance=models.Distance.COSINE
                ),
            )

    async def get_db_info(self):
        return self.client.get_collection(collection_name=COLLECTION_NAME)

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
<<<<<<< HEAD
    app = PlacesApplication(**args)
=======
    # XXX convert args into kw
    app = PlacesApplication()
>>>>>>> 189de3a (savepoint)
    app.add_routes(routes)
    app.init_db()
    print("Starting semantic bookmarks server...")
    web.run_app(app, port=8080)
