import asyncio
import sqlite3
from urllib.parse import urlparse
from uuid import uuid4
import sys

import numpy
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from places.extractor import Extractor
from places.scrap import WebScrap


COLLECTION_NAME = "pages"


skip = (
    "github.com",
    "google.com",
    "compute.amazonaws.com",
    "googleadservices.com",
    "dartsearch",
    "facebook.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
)


class Places:
    def __init__(self, queue, db="places.sqlite"):
        self.db = db
        self.queue = queue

    async def run(self):
        # blocking code
        con = sqlite3.connect("places.sqlite")
        cur = con.cursor()
        print("[places] Reading places.sqlite")
        count = 0
        for line in cur.execute("select URL from moz_places"):
            url = line[0]
            if self.to_skip(url):
                continue
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                count += 1
                await self.queue.put(url)

        print(f"[places] Collected {count} urls")
        await self.queue.put("END")

    def to_skip(self, url):
        for skipped in skip:
            if skipped in url:
                return True
        return False


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


async def main(db_path):
    urls = asyncio.Queue()
    pages = asyncio.Queue()
    vectors = asyncio.Queue()

    coros = []

    # Places feeds the urls queue
    coros.append(Places(urls, db=db_path).run())

    # Webscrap converts urls into pages
    coros.append(WebScrap(urls, pages).run())

    # Extractor reads from urls and feeds vectors
    coros.append(Extractor(pages, vectors).run())

    # Upserter reads from vectors and sends to QDrant
    coros.append(Upserter(vectors).run())

    # let's start everyone
    await asyncio.gather(*coros)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[-1]))
