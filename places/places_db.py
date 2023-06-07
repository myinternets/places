import json
import sqlite3
from urllib.parse import urlparse
from diskcache import Cache
from utils import remove_bom

# TODO: replace this with a sophisticated list
# (regex, blacklists, patterns etc.)
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


class SessionBuddy:
    """
    SessionBuddy class to read URLs from a Session Buddy JSON export.
    Refer to Chrome plugin: Session Buddy (https://sessionbuddy.com/)

    Parameters:
    @queue: An asyncio queue to put the read URLs into.
    @db: The path to the Session Buddy JSON export file.
    @cache: An optional cache to check for duplicate URLs. Default is an empty dict.

    Functionality:
    - Reads the Session Buddy JSON export file
      (and modifies it to remove BOM at read time)
    - Extracts URLs from the "current" session (TODO: read all sessions).
    - Puts all non-skipped URLs into the queue.
    - Skips URLs that:
        - Contain a domain in the skip list (github.com, google.com, etc.)
        - Are already in the cache
    - Prints stats on the number of URLs collected and skipped.
    - Puts "END" into the queue when done.
    """

    def __init__(self, queue, db="session.json", cache=None):
        self.db = db
        self.queue = queue
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache
        remove_bom(self.db)

    async def run(self):
        session_data = {}
        try:
            with open(self.db, 'r', encoding='utf-8-sig') as f:
                session_data = json.load(f)
        except FileNotFoundError:
            print("File not found")
            await self.queue.put("END")
        except json.JSONDecodeError:
            print("JSON decoding error")
            await self.queue.put("END")

        print("[places] Reading session buddy json export")

        if session_data:
            # TODO: process all saved sessions. [0] only gets "current".
            browser_windows = session_data["sessions"][0]['windows']

            url_count = 0
            skipped_count = 0
            for window in browser_windows:
                tabs = window['tabs']
                for tab in tabs:
                    url = tab['url']
                    title = tab['title']
                    if self.should_skip(url):
                        skipped_count += 1
                        continue
                    self.cache[url] = title
                    parsed = urlparse(url)
                    if parsed.scheme in ("http", "https"):
                        url_count += 1
                        await self.queue.put(url)

            print(f"[sessionbuddy] Collected {url_count} urls. Skipped {skipped_count} urls")
        await self.queue.put("END")

    def should_skip(self, url):
        for skipped in skip:
            if skipped in url:
                return True
        if url in self.cache:
            if self.cache[url] != "error":
                return True
        return False


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
            if self.to_skip(url):
                skipped_count += 1
                continue
            self.cache[url] = "processing"
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                url_count += 1
                await self.queue.put(url)

        print(f"[places] Collected {url_count} urls. Skipped {skipped_count} urls")
        await self.queue.put("END")

    def to_skip(self, url):
        for skipped in skip:
            if skipped in url:
                return True
        if url in self.cache:
            if self.cache[url] != "error" and self.cache[url] != "unreadable":
                return True
        return False