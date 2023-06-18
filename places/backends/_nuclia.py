from nucliadb_models.metadata import InputMetadata, Origin
from nucliadb_models.text import TextField, TextFormat
from nucliadb_models.writer import CreateResourcePayload
from nucliadb_protos.resources_pb2 import FieldType
from nucliadb_protos.utils_pb2 import Vector
from nucliadb_client.client import NucliaDBClient
from nucliadb_models.search import SearchRequest, KnowledgeboxSearchResults
import json


class NucliaDB:
    def __init__(self, **kw):
        self.nucliadb_base_url = kw.pop("nucliadb_base_url", "http://localhost:8080")
        self.client = NucliaDBClient(host="localhost", grpc=8060, http=6333)
        self.kb = self.client.get_kb(slug="places")
        if self.kb is None:
            self.kb = self.client.create_kb(slug="places", title="Browser History")

    async def search(self, query_vector, limit=10, query=None):
        payload = SearchRequest()
        payload.vector = query_vector
        payload.min_score = 0.05

        response = self.kb.http_search_v1.post(
            "search", content=payload.json().encode()
        )

        data = json.loads(response.content)

        if response.status_code != 200:
            print(json.dumps(data, indent=2))
            raise Exception(str(response.status_code))

        try:
            hits = KnowledgeboxSearchResults.parse_raw(response.content)
        except Exception:
            print(json.dumps(data, indent=2))
            raise

        hits = hits.dict()

        for sentence in hits["sentences"]["results"]:
            rid = sentence["rid"]
            resource = hits["resources"][rid]
            url = resource["metadata"].get("metadata", {}).get("url")
            sentence.update(resource)
            sentence["sentence"] = sentence["text"]
            sentence["url"] = url
            yield sentence

    async def index(self, points, **kw):
        payload = CreateResourcePayload()

        payload.title = kw["title"]
        payload.icon = "text/html"
        payload.metadata = InputMetadata()
        payload.metadata.language = "en"

        # not sure where to store the URL
        payload.metadata.metadata = {"url": kw["url"]}
        payload.origin = Origin()
        payload.origin.url = kw["url"]

        field = TextField(body=kw["text"])
        field.format = TextFormat.HTML
        payload.texts["body"] = field

        resource = self.kb.create_resource(payload)

        pure_text = " ".join(kw["sentences"])
        resource.add_text("body", FieldType.TEXT, pure_text)

        vectors = []
        index = 0
        for sentence, embedding in points:
            vector = Vector(
                start=index,
                end=index + len(sentence),
                start_paragraph=0,
                end_paragraph=len(pure_text),
            )
            index += len(sentence) + 1
            vector.vector.extend(embedding)
            vectors.append(vector)

        resource.add_vectors(
            "body",
            FieldType.TEXT,
            vectors,
        )
        resource.sync_commit()

    def create_point(self, index, url, title, vec, sentence):
        return sentence, vec

    def init_db(self):
        pass

    async def get_db_info(self):
        counters = self.kb.counters()
        info = {"name": "NucliaDB", "vectors_count": counters.sentences}
        return info
