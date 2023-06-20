import json
from urllib.parse import urlparse

from places.utils import remove_bom, should_skip


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
            with open(self.db, "r", encoding="utf-8-sig") as f:
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
            browser_windows = session_data["sessions"][0]["windows"]

            url_count = 0
            skipped_count = 0
            for window in browser_windows:
                tabs = window["tabs"]
                for tab in tabs:
                    url = tab["url"]
                    title = tab["title"]
                    if self.should_skip(url):
                        skipped_count += 1
                        continue
                    self.cache[url] = title
                    parsed = urlparse(url)
                    if parsed.scheme in ("http", "https"):
                        url_count += 1
                        await self.queue.put(url)

            print(
                f"[sessionbuddy] Collected {url_count} urls. Skipped {skipped_count} urls"
            )
        await self.queue.put("END")

    def should_skip(self, url):
        if should_skip(url):
            return True
        if url in self.cache:
            if self.cache[url] != "error":
                return True
        return False
