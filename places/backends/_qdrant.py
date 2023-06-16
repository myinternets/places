import hashlib

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct


class QDrantDB:
    def __init__(self, **kw):
        self.host = kw.pop("qdrant_host", "localhost")
        self.port = kw.pop("qdrant_port", 6333)
        self.client = QdrantClient(host=self.host, port=self.port)
        self._collection_name = "pages"

    async def search(self, query_vector, limit=10):
        hits = self.client.search(
            self._collection_name, query_vector=query_vector, limit=limit
        )
        for hit in hits:
            yield hit.payload

    async def index(self, points):
        return self.client.upsert(
            collection_name=self._collection_name,
            points=points,
        ).json()

    def create_point(self, index, url, title, vec, sentence):
        point_id = hashlib.md5(f"{url}-{index}".encode()).hexdigest()
        return PointStruct(
            id=point_id,
            vector=vec,
            payload={"url": url, "sentence": sentence, "title": title},
        )

    def init_db(self):
        try:
            self.client.get_collection(collection_name=self._collection_name)
            return
        except Exception:
            self.client.recreate_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=384, distance=models.Distance.COSINE
                ),
            )

    async def get_db_info(self):
        info = dict(self.client.get_collection(collection_name=self._collection_name))
        info["name"] = "QDrant"
        return info
