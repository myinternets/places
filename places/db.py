import asyncio
import os
import hashlib
import json
import time
from urllib.parse import urlparse
from contextlib import asynccontextmanager

import aiosqlite
from places.config import URL_SKIP_LIST


class Pages:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def get_path(self, url):
        url_id = hashlib.md5(url.encode("utf8")).hexdigest()
        return os.path.join(self.root_dir, url_id)

    def get_ts(self, url):
        return self.get(url)["ts"]

    def get(self, url):
        path = self.get_path(url)
        if os.path.exists(path):
            with open(path) as f:
                return json.loads(f.read())
        else:
            raise KeyError(f"{url} {path}")

    def set(self, url, data, ts=None):
        if ts is None:
            ts = time.time()
        path = self.get_path(url)

        if os.path.exists(path):
            doc_data = self.get(url)
            doc_data.update(data)
        else:
            doc_data = data

        doc_data["ts"] = ts
        doc_data["url"] = url

        print(f"Storing {url} in {path}")
        with open(path, "w") as f:
            f.write(json.dumps(doc_data))


_CREATION = """\
CREATE TABLE IF NOT EXISTS domain (
  domain TEXT PRIMARY KEY NOT NULL,
  skip BOOL DEFAULT FALSE,
  indexed_pages INTEGER DEFAULT 0
  )
"""


class DB:
    def __init__(self, path="places-db.sqlite"):
        self.path = path

    @asynccontextmanager
    async def session(self):
        async with aiosqlite.connect(self.path) as db:
            try:
                yield db
            finally:
                await db.commit()

    async def check_db(self):
        async with self.session() as db:
            await db.execute(_CREATION)
        for url in URL_SKIP_LIST:
            print(f"Adding {url} to skip list")
            await self.set_skip(url)

    def get_domain(self, url):
        if url.startswith("http"):
            return urlparse(url).netloc
        return url

    async def set_skip(self, url, skip=True):
        info = await self.domain_info(url)
        info["skip"] = skip
        await self._save_domain(info)

    async def get_skip(self, url):
        info = await self.domain_info(url)
        return info["skip"]

    async def _save_domain(self, domain):
        skip = 1 if domain["skip"] else 0

        async with self.session() as db:
            await db.execute(
                "UPDATE domain SET skip = ?, indexed_pages = ? WHERE domain = ?",
                (skip, domain["indexed_pages"], domain["domain"]),
            )

    async def indexed(self, url):
        domain = self.get_domain(url)

        async with self.session() as db:
            await db.execute(
                "UPDATE domain SET indexed_pages = indexed_pages +  1 WHERE domain = ?",
                (domain,),
            )

    async def add_domain(self, url):
        domain = self.get_domain(url)
        async with self.session() as db:
            await db.execute("INSERT INTO domain (domain) values (?)", (domain,))

    async def domain_info(self, url):
        domain = self.get_domain(url)

        async with self.session() as db:
            cursor = await db.execute(
                "SELECT * from domain WHERE domain = ?", (domain,)
            )
            row = await cursor.fetchone()
            if row is None:
                await db.execute("INSERT INTO domain (domain) values (?)", (domain,))
                return {"domain": domain, "skip": False, "indexed_pages": 0}
            _, skip, indexed_pages = row
            skip = True if skip == 1 else False
            return {"domain": domain, "skip": skip, "indexed_pages": indexed_pages}


if __name__ == "__main__":

    async def test_db():
        db = DB()
        await db.check_db()

        assert await db.get_skip("http://example.com")
        await db.indexed("http://example.com")
        print(await db.domain_info("http://example.com"))
        await db.indexed("http://example.com")
        print(await db.domain_info("http://example.com"))

        await db.set_skip("example.com", True)
        assert not (await db.get_skip("http://example.com"))
        await db.set_skip("http://example.com", False)
        assert await db.get_skip("http://example.com")

    asyncio.run(test_db())
