from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from uuid import uuid4
import numpy

COLLECTION_NAME = "pages"


class Upserter:
    def __init__(self, queue):
        self.queue = queue
        self.client = QdrantClient(host="localhost", port=6333)
        self.client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    async def run(self):
        idx = 1

        while True:
            data = await self.queue.get()
            if data == "END":
                return

            url, vectors, sentences, summary = data

            print(f"[upsert] {url}")
            points = []

            for vec, sentence in zip(vectors, sentences):
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector=list(numpy.asfarray(vec)),
                        payload={"url": url, "sentence": sentence},
                    )
                )

            try:
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points,
                )

                idx += 1
            except Exception:
                print(f"[upsert] failed for {url}")
