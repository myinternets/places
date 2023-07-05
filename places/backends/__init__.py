from places.backends._qdrant import QDrantDB
from places.backends._vectra import LocalDB
from places.backends._nuclia import NucliaDB


def get_db(**kw):
    if kw["db"] == "qdrant":
        return QDrantDB(**kw)
    elif kw["db"] == "nuclia":
        return NucliaDB(nucliadb_base_url="http://localhost:6333", **kw)
    return LocalDB(**kw)
