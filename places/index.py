import asyncio
import sys

from places.extractor import Extractor
from places.scrap import WebScrap
from places.places_db import Places
from places.vector_db import Upserter


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
