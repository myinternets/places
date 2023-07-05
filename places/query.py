import sys

import numpy
from sentence_transformers import SentenceTransformer
from places.backends import get_db


model = SentenceTransformer("all-MiniLM-L6-v2")
client = get_db(db="qdrant")


def query(sentence):
    embedding = model.encode([sentence])
    vector = numpy.asfarray(embedding[0])
    vector = list(vector)

    hits = client.search(query_vector=vector, limit=3)

    for i, hit in enumerate(hits):
        print(f"{i}. {hit.payload['url']}")
        print()
        print(hit.payload["sentence"])
        print()
        print()


if __name__ == "__main__":
    query(sys.argv[-1])
