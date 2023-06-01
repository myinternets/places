import functools

import aiohttp

from places.utils import task_pool

supported = [
    "text/html",
]


class WebScrap:
    def __init__(self, urls, pages, source="firefox", cache={}):
        self.urls = urls
        self.source = source
        self.cache = cache
        self.pages = pages
        self._tasks = []

    async def get_url(self, client, url):
        # print(f"[scrap] reading {url}")
        try:
            async with client.head(url) as resp:
                ct = resp.content_type

            if ct not in supported:
                return None

            async with client.get(url) as resp:
                for history in resp.history:
                    if history.status > 399:
                        return None

                text = await resp.text()
                self.cache[url] = "processed"
                return url, text
        except Exception as e:
            print(f"[scrap] Could not read {url} {e}")
            if self.source == "sessionbuddy":
                title = self.cache.get(url)
                self.cache[url] = "unreadable"
                return url, title
            else:
                self.cache[url] = "error"
                return None

    def url_fetched(self, result):
        if result is None:
            return
        self.pages.put_nowait(result)

    async def run(self):
        async with task_pool() as tasks:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as client:
                while True:
                    url = await self.urls.get()
                    if url == "END":
                        await self.pages.put("END")
                        return

                    await tasks.put(
                        functools.partial(self.get_url, client, url), self.url_fetched
                    )
