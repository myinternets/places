import json

from places.vectors import build_vector

_HTML_PAGE = """\
<html>
  <head><title>The title</title></head>
  <body>Some text</body>
</html>
"""


def test_build_vector():
    data = {"url": "http://example.com", "text": _HTML_PAGE}

    res = json.loads(build_vector(json.dumps(data)))

    assert res["sentences"] == ["The title Some text"]
    assert len(res["vectors"][0]) == 384
    assert res["title"] == "The title"
