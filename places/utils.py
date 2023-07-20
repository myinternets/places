import asyncio
import functools
import os
import re
from contextlib import asynccontextmanager
from functools import cache
from urllib.parse import urlparse

import fasttext
import nltk
import numpy as np
from bs4 import BeautifulSoup
from nltk.langnames import langname
from sentence_transformers import util
from transformers import pipeline

from places.config import URL_SKIP_LIST
from places.lexrank import degree_centrality_scores

_QA = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")


_WEBEXT_VERSION = None


def called_by(version):
    global _WEBEXT_VERSION
    _WEBEXT_VERSION = version


def get_webext_version():
    return _WEBEXT_VERSION


def extract_text(filename):
    if not filename.endswith(".pdf"):
        print(f"Skipping {filename}, extension not supported")
    # use pdf2text and others, so we don't blow the mem
    # return text
    import pdftotext

    print(f"Extracting {filename}")
    with open(filename, "rb") as f:
        pdf = pdftotext.PDF(f)
        return "\n\n".join(pdf).strip()


def should_skip(url, cache=None):
    url_hostname = urlparse(url).hostname
    if url_hostname in URL_SKIP_LIST:
        return True
    if cache is not None:
        if url in cache:
            if cache[url] != "error" and cache[url] != "unreadable":
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
    return title, tokenize(text, lang), lang, text


@cache
def answer(question, context):
    return _QA(context=context, question=question)


def build_answer(url, question, text):
    print(f"Building answer for {url}")
    a = answer(question, text)
    # XXX UGLY
    # grabbing the surroundings of the answer
    n_start = a["start"]
    n_end = a["end"]
    while text[n_start] != "\n" and n_start > 0:
        n_start -= 1
    while text[n_end] != "\n" and n_end < len(text):
        n_end += 1
    extract = text[n_start:n_end]
    extract = extract.replace(a["answer"], f'<span class="answer">{a["answer"]}</span>')
    return {
        "answer": a["answer"],
        "url": url,
        "score": a["score"],
        "extract": extract,
    }
