import aiohttp
import functools
import ujson

from places.utils import task_pool


class Upserter:
    def __init__(self, queue, server="http://localhost:8080"):
        self.queue = queue
        self.server = server

    async def post_url(self, client, url, text):
        try:
            doc = {"url": url, "text": text}

            async with client.post(f"{self.server}/index", json=doc) as resp:
                res = await resp.json()
                if resp.status > 299:
                    print(res["error"])
                    return None
        except Exception as e:
            print(f"[scrap] Could not post {url} {e}")
            return None

    async def run(self):
        async with task_pool() as tasks:
            async with aiohttp.ClientSession(
                json_serialize=ujson.dumps, timeout=aiohttp.ClientTimeout(total=15)
            ) as client:
                while True:
                    res = await self.queue.get()
                    if res == "END":
                        await self.queue.put("END")
                        return

                    url, text = res

                    await tasks.put(functools.partial(self.post_url, client, url, text))
