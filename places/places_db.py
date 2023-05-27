import sqlite3
from urllib.parse import urlparse

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
        con = sqlite3.connect(self.db)
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
