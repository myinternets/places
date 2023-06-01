import os
import sys
import asyncio
from diskcache import Cache

from places.vectors import Upserter
from places.scrap import WebScrap
from places.places_db import Places, SessionBuddy

CACHE_DIR = os.path.join(os.path.expanduser('~/.cache'), 'places')

def initiate_cache(source):
    """
    This aims to have a persistent cache to avoid re-reading urls.
    TODO: could be set to the same folder to synchronize URL cache between
    different sources.
    """
    # make a cache in ~/.cache/places
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    # TODO: brainstorm cache performance considerations for long urls
    cache = Cache(os.path.join(CACHE_DIR, source))
    return cache


async def main(db_path):
    urls = asyncio.Queue()
    pages = asyncio.Queue()

    coros = []
    source = None

    # check if ends with .sqlite or .json
    if db_path.endswith(".sqlite"):
        # Places feeds the urls queue
        source = "firefox"
        cache = initiate_cache(source)
        coros.append(Places(urls, db=db_path, cache=cache).run())
    elif db_path.endswith(".json"):
        # SessionBuddy feeds the urls queue
        source = "sessionbuddy"
        cache = initiate_cache(source)
        coros.append(SessionBuddy(urls, db=db_path, cache=cache).run())
    else:
        raise ValueError(f"Unknown source of bookmarks db {db_path}")

    # Webscrap converts urls into pages
    coros.append(WebScrap(urls, pages, source=source).run())

    # Upserter reads from pages and sends to web api
    coros.append(Upserter(pages).run())

    # let's start everyone
    await asyncio.gather(*coros)


if __name__ == "__main__":
    bookmarks_path = sys.argv[-1]
    asyncio.run(main(bookmarks_path))