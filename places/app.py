"""
  Web App
"""
import asyncio
import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from places.backends import get_db
from places.db import DB, Pages
from places.vectors import model
from places.utils import get_webext_version


HERE = os.path.dirname(__file__)


class PlacesApplication(web.Application):
    def __init__(self, args):
        super().__init__(client_max_size=None)
        self.env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")))
        self.client = get_db(**args)
        self.executor = ProcessPoolExecutor()
        self.on_startup.append(self._startup)
        self.on_cleanup.append(self._cleanup)
        self.pages_db = Pages("/tmp/pages")
        self.db = DB()

    async def _startup(self, app):
        self["loop"] = asyncio.get_running_loop()
        await self.db.check_db()

    async def _cleanup(self, app):
        self.executor.shutdown()

    async def query(self, sentence):
        # vectorize the query
        embedding = await self.run_in_executor(model.encode, [sentence])
        vector = numpy.asfarray(embedding[0])
        vector = list(vector)
        hits = []
        async for hit in self.client.search(query_vector=vector, limit=10):
            hits.append(hit)
        return hits

    def init_db(self):
        self.client.init_db()

    async def get_db_info(self):
        return await self.client.get_db_info()

    async def html_resp(self, template, status=200, **args):
        template = self.env.get_template(template)
        args["db_info"] = await self.get_db_info()
        args["args"] = ({"title": "My Internets"},)
        args["description"] = "Search Your History"
        args["webext_version"] = get_webext_version()
        content = template.render(**args)
        resp = web.Response(text=content)
        resp.headers["Content-Type"] = "text/html"
        resp.set_status(status)
        return resp

    async def json_resp(self, body, status=200):
        if not isinstance(body, str):
            body = json.dumps(body)
        resp = web.Response(text=body)
        resp.headers["Content-Type"] = "application/json"
        resp.set_status(status)
        return resp

    def task_executor(self, function, *args, **kw):
        return self["loop"].run_in_executor(self.executor, function, *args, **kw)

    async def run_in_executor(self, function, *args, **kw):
        task = self["loop"].run_in_executor(self.executor, function, *args, **kw)
        await task

        if task.exception() is not None:
            raise task.exception()

        return task.result()
