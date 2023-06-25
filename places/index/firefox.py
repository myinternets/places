import sqlite3
from urllib.parse import urlparse

from places.utils import should_skip


class Places:
    """
    Places class to read URLs from a places.sqlite database.
    Refer to https://wiki.mozilla.org/Places

    Parameters:
    @queue: An asyncio queue to put the read URLs into.
    @db: The path to the places.sqlite database file. Default is "places.sqlite".
    @cache: An optional cache to check for duplicate URLs. Default is None.

    Functionality:
    - Reads the places.sqlite database.
    - Extracts URLs from the moz_places table.
    - Puts all non-skipped URLs into the queue.
    - Skips URLs that:
        - Contain a domain in the skip list (github.com, google.com, etc.)
        - Are already in the cache
    - Prints stats on the number of URLs collected and skipped.
    - Puts "END" into the queue when done.
    """

    def __init__(self, queue, db="places.sqlite", cache=None):
        self.db = db
        self.queue = queue
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache

    async def run(self):
        # blocking code
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("[places] Reading places.sqlite")
        url_count = 0
        skipped_count = 0
        for line in cur.execute("select URL from moz_places"):
            url = line[0]
            if should_skip(url, cache=self.cache):
                skipped_count += 1
                continue
            self.cache[url] = "processing"
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                url_count += 1
                await self.queue.put(url)

        print(f"[places] Collected {url_count} urls. Skipped {skipped_count} urls")
        await self.queue.put("END")
