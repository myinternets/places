import sys

import numpy
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer("all-MiniLM-L6-v2")


COLLECTION_NAME = "pages"


def query(sentence):
    embedding = model.encode([sentence])
    vector = numpy.asfarray(embedding[0])
    vector = list(vector)

    hits = client.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=3)

    for i, hit in enumerate(hits):
        print(f"{i}. {hit.payload['url']}")
        print()
        print(hit.payload["sentence"])
        print()
        print()


if __name__ == "__main__":
    query(sys.argv[-1])
