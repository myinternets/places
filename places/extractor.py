from multiprocessing import current_process
import json

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


def build_vector(data):
    """Vectorizes a page.

    1. Extracts the title and text using BeautifulSoup
    2. Segmentizes the text
    3. Create embeddings for each sentences using SentenceTransformer

    Accepts a JSON-encoded mapping containing the url and text.
    The data is passed as a string so it can be pickled.

    Returns a JSON-encoded mapping containing:

    - vectors: a list of vectors
    - sentences: a list of sentences
    - title: the title of the page

    """

    data = json.loads(data)
    url = data["url"]
    text = data["text"]

    cp = current_process()
    print(f"[extractor][{cp.pid}] working on {url}")
    soup = BeautifulSoup(text, "html.parser")

    try:
        title = soup.title
        if title is None:
            title = ""
        else:
            title = title.string
    except Exception:
        title = ""

    try:
        text = soup.get_text()
    except Exception as e:
        print(f"Could not extract the content of {url} - bs4 error")
        raise Exception(f"Could not extract the content of {url}") from e

    # _summary = summary(text)
    try:
        sentences = segmentation(text)
    except Exception as e:
        msg = f"Could not segmentize {url}"
        print(msg)
        raise Exception(msg) from e

    try:
        vectors = model.encode(sentences)
    except Exception as e :
        msg = f"Could not encode with the model {url}"
        print(msg)
        raise Exception(msg) from e

    return json.dumps(
        {"vectors": vectors.tolist(), "sentences": sentences, "title": title}
    )
