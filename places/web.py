import os

import numpy
from bottle import request, route, run
from jinja2 import Environment, FileSystemLoader
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

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


run(host="localhost", port=8080)
