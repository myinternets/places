import asyncio
import concurrent
from multiprocessing import current_process
import functools

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from txtai.pipeline import Summary
from txtai.pipeline.data import Segmentation

from places.utils import task_pool


print("Loading models")

model = SentenceTransformer("all-MiniLM-L6-v2")
summary = Summary("sshleifer/distilbart-cnn-12-6")
segmentation = Segmentation(sentences=True)


def bs_parse(content="", parser="html.parser"):
    soup = BeautifulSoup(content, parser)
    return soup.get_text()


def build_vector(url, text):
    cp = current_process()
    print(f"[extractor][{cp.pid}] working on {url}")
    text = bs_parse(text)
    _summary = summary(text)
    sentences = segmentation(_summary)
    vectors = model.encode(sentences)
    return vectors, sentences, _summary


class Extractor:
    def __init__(self, pages, vectors):
        self.pages = pages
        self.vectors = vectors

    def vector_ready(self, result):
        if result is None:
            return
        self.vectors.put_nowait(result)

    async def vectorize(self, pool, url, text):
        # cpu-bound
        loop = asyncio.get_running_loop()
        vectors, sentences, _summary = await loop.run_in_executor(
            pool, build_vector, url, text
        )
        return url, vectors, sentences, _summary

    async def run(self):
        async with task_pool() as tasks:
            with concurrent.futures.ProcessPoolExecutor(max_workers=15) as pool:
                while True:
                    page = await self.pages.get()
                    if page == "END":
                        await self.vectors.put("END")
                        return

                    url, text = page
                    await tasks.put(
                        functools.partial(self.vectorize, pool, url, text),
                        self.vector_ready,
                    )
