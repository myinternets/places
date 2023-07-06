import os
import hashlib
import json
import time


class Pages:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def get_path(self, url):
        url_id = hashlib.md5(url.encode("utf8")).hexdigest()
        return os.path.join(self.root_dir, url_id)

    def get_ts(self, url):
        return self.get(url)["ts"]

    def get(self, url):
        path = self.get_path(url)
        if os.path.exists(path):
            with open(path) as f:
                return json.loads(f.read())
        else:
            raise KeyError(f"{url} {path}")

    def set(self, url, data, ts=None):
        if ts is None:
            ts = time.time()
        path = self.get_path(url)

        if os.path.exists(path):
            doc_data = self.get(url)
            doc_data.update(data)
        else:
            doc_data = data

        doc_data["ts"] = ts
        doc_data["url"] = url

        print(f"Storing {url} in {path}")
        with open(path, "w") as f:
            f.write(json.dumps(doc_data))
