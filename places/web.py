import os
import json
from uuid import uuid4

import numpy
from bottle import request, route, run, post, response
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


def query(sentence):
    embedding = model.encode([sentence])
    vector = numpy.asfarray(embedding[0])
    vector = list(vector)

    hits = client.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=3)
    return hits


# XXX Sync API for now
@post("/index")
def index_doc():
    response.content_type = "application/json"
    response.status = 200

    try:
        data = request.json
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

        return client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        ).json()
    except Exception as e:
        response.status = 400
        return json.dumps({"error": str(e)})


@route("/search")
def search():
    q = request.query["q"]
    hits = query(q)
    template = environment.get_template("index.html")
    args = {
        "args": {"title": "Private Search"},
        "description": "Search Your History",
        "hits": hits,
        "query": q,
    }
    content = template.render(**args)
    return content


@route("/")
def index():
    template = environment.get_template("index.html")
    args = {"args": {"title": "Private Search"}, "description": "Search Your History"}
    content = template.render(**args)
    return content


if __name__ == "__main__":
    run(host="0.0.0.0", port=8080)
