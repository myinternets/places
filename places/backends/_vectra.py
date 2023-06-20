import hashlib

from places.backends.vectra import LocalIndex


# could use https://github.com/spotify/annoy instead
class LocalDB:
    def __init__(self, **kw):
        self.path = kw["vectra_path"]
        self._index = LocalIndex(self.path)
        self._collection_name = "pages"

    async def search(self, query_vector, limit=10):
        hits = await self._index.query_items(query_vector, limit)
        for hit in hits:
            data = hit["item"]["metadata"]
            yield data

    def init_db(self):
        if not self._index.is_index_created():
            self._index.create_index()

    async def get_db_info(self):
        stats = await self._index.get_index_stats()
        return {"name": f"Vectra v{stats['version']}", "vectors_count": stats["items"]}

    def create_point(self, index, url, title, vec, sentence):
        point_id = hashlib.md5(f"{url}-{index}".encode()).hexdigest()
        metadata = {"url": url, "title": title, "sentence": sentence}
        return {"id": point_id, "metadata": metadata, "vector": vec}

    async def index(self, points):
        res = []
        for point in points:
            res.append(await self._index.upsert_item(point))
        return res
