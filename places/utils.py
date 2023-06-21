import asyncio
import functools
from contextlib import asynccontextmanager
import os
import re

import numpy as np
from sentence_transformers import util
import fasttext
from nltk.langnames import langname
import nltk
from bs4 import BeautifulSoup

from places.lexrank import degree_centrality_scores


# TODO: replace this with a sophisticated list
# (regex, blocklists, patterns etc.)
_SKIP = (
    "github.com",
    "https://google.com",
    "compute.amazonaws.com",
    "googleadservices.com",
    "dartsearch",
    "facebook.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
)


def should_skip(url):
    for skipped in _SKIP:
        if skipped in url:
            return True
    return False


class Tasks:
    def __init__(self, concurrency=5, cb=None):
        self.concurrency = concurrency
        self.tasks = []
        self.cb = cb
        self._done = asyncio.Event()

    def _callback(self, task, cb=None):
        self.tasks.remove(task)
        self._done.set()
        if task.exception():
            print(f"Exception found for task {task.get_name()}: {task.exception()}")
        if cb is not None:
            cb(task.result())
        if self.cb is not None:
            self.cb(task.result())

    async def put(self, coroutine, cb=None):
        if len(self.tasks) >= self.concurrency:
            await self._done.wait()
            self._done.clear()
        task = asyncio.create_task(coroutine())
        self.tasks.append(task)
        task.add_done_callback(functools.partial(self._callback, cb=cb))
        return task

    async def join(self):
        await asyncio.gather(*self.tasks, return_exceptions=True)

    def cancel(self):
        for task in self.tasks:
            task.cancel()


@asynccontextmanager
async def task_pool(max_tasks=10, cb=None):
    tasks = Tasks(max_tasks, cb)
    try:
        yield tasks
    finally:
        await tasks.join()


def remove_bom(file_path):
    """
    Session buddy exports have Byte Order Mark (BOMs)
    at the start of the file. Currently, it has duplicate
    such BOMs which renders encoding="utf-8-sig" useless.
    This method removes them recursively.
    """
    with open(file_path, "rb") as f:
        content = f.read()
    bom = b"\xef\xbb\xbf"
    removed = False
    # current exports have duplicate BOMs
    while content.startswith(bom):
        content = content[len(bom) :]
        removed = True
    if removed:
        print(f"...removed BOM from {file_path}")
        with open(file_path, "wb") as f:
            f.write(content)
    else:
        print(f"...no BOM found in {file_path}")


def sort_by_centrality(embeddings):
    cos_scores = util.cos_sim(embeddings, embeddings).numpy()
    centrality_scores = degree_centrality_scores(cos_scores, threshold=None)
    most_central_sentence_indices = np.argsort(-centrality_scores)
    return most_central_sentence_indices


_LANG_MODEL = fasttext.load_model(
    os.path.join(os.path.dirname(__file__), "lid.176.ftz")
)

nltk.download("punkt")
nltk.download("bcp47")


def detect_lang(text):
    try:
        predictions = _LANG_MODEL.predict(text.replace("\n", " "), k=1)
        lang = predictions[0][0].split("__")[-1]
        return langname(lang).lower()
    except Exception:
        # will do better later
        return "english"


_RE_TEXT = re.compile(r"\s+")


def tokenize(text, lang=None):
    if lang is None:
        lang = detect_lang(text)
    for sentence in nltk.sent_tokenize(text, language=lang):
        sentence = _RE_TEXT.sub(" ", sentence).strip()
        if sentence == "":
            continue
        yield sentence


def tokenize_html(html):
    soup = BeautifulSoup(html, "html.parser")
    try:
        title = soup.title
        if title is None:
            title = ""
        else:
            title = title.string
    except Exception:
        title = ""

    title = _RE_TEXT.sub(" ", title).strip()
    text = soup.get_text()
    lang = detect_lang(text)
    return title, tokenize(text, lang), lang
