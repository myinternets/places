from multiprocessing import current_process

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

# from txtai.pipeline import Summary
from txtai.pipeline.data import Segmentation
import nltk

nltk.download("punkt")

model = SentenceTransformer("all-MiniLM-L6-v2")
# this line segfaults in Docker for some reason
# summary = Summary("sshleifer/distilbart-cnn-12-6")
segmentation = Segmentation(sentences=True)


def bs_parse(content="", parser="html.parser"):
    soup = BeautifulSoup(content, parser)
    return soup.get_text()


def build_vector(url, text):
    cp = current_process()
    print(f"[extractor][{cp.pid}] working on {url}")
    text = bs_parse(text)
    # _summary = summary(text)
    sentences = segmentation(text)
    vectors = model.encode(sentences)
    return vectors, sentences, text
