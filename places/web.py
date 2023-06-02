import os
import json
from uuid import uuid4
import logging

from aiohttp import web
import numpy
from jinja2 import Environment, FileSystemLoader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

from places.extractor import build_vector


HERE = os.path.dirname(__file__)
model = SentenceTransformer("all-MiniLM-L6-v2")
COLLECTION_NAME = "pages"
environment = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")))
client = QdrantClient(host="localhost", port=6333)
routes = web.RouteTableDef()
logging.getLogger("asyncio").setLevel(logging.DEBUG)


def query(sentence):
    embedding = model.encode([sentence])
    vector = numpy.asfarray(embedding[0])
    vector = list(vector)
    hits = client.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=3)
    return hits


def json_resp(body, status=200):
    if not isinstance(body, str):
        body = json.dumps(body)
    resp = web.Response(text=body)
    resp.headers["Content-Type"] = "application/json"
    resp.set_status(status)
    return resp


def html_resp(template, status=200, **args):
    template = environment.get_template(template)
    content = template.render(**args)
    resp = web.Response(text=content)
    resp.headers["Content-Type"] = "text/html"
    resp.set_status(status)
    return resp


@routes.post("/index")
async def index_doc(request):
    try:
        data = await request.json()

        # CPU-bound
        vectors, sentences, summary = build_vector(data["url"], data["text"])
        points = []

        for vec, sentence in zip(vectors, sentences, strict=True):
            points.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=list(numpy.asfarray(vec)),
                    payload={"url": data["url"], "sentence": sentence},
                )
            )

        return json_resp(
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
            ).json()
        )
    except Exception as e:
        return json_resp({"error": str(e)}, 400)


@routes.get("/search")
async def search(request):
    q = request.query["q"]
    hits = query(q)
    args = {
        "args": {"title": "Private Search"},
        "description": "Search Your History",
        "hits": hits,
        "query": q,
    }
    return html_resp("index.html", **args)


@routes.get("/")
async def index(request):
    args = {"args": {"title": "Private Search"}, "description": "Search Your History"}
    return html_resp("index.html", **args)


app = web.Application()
app.add_routes(routes)


if __name__ == "__main__":
    web.run_app(app, port=8080)
