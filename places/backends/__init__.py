from places.backends._qdrant import QDrantDB
from places.backends._vectra import LocalDB


def get_db(**kw):
    if kw["db"] == "qdrant":
        return QDrantDB(**kw)
    return LocalDB(**kw)
