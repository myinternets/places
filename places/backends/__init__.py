from places.backends._vectra import LocalDB
from places.backends._qdrant import QDrantDB


def get_db(**kw):
    if kw["db"] == "qdrant":
        return QDrantDB(**kw)
    return LocalDB(**kw)
