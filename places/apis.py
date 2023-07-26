"""
API routes
"""
import asyncio
import json
import time
import traceback as tb

import numpy
from aiohttp import web

from places.utils import called_by, extract_text
from places.vectors import build_vector

apis = web.RouteTableDef()


def error_to_json(e):
    return {
        "error": repr(e),
        "tb": "".join(tb.format_exception(None, e, e.__traceback__)),
    }


@apis.post("/index")
async def index_doc(request):
    try:
        data = await request.json()

        called_by(data.get("webext_version", "0.0.1"))
        url = data["url"]
        if await request.app.db.get_skip(url):
            print(f"Skipping {url}")
            return await request.app.json_resp({"result": "skipped domain"}, 200)

        # is this a filename ?
        if "filename" in data:
            # only works locally
            data["text"] = extract_text(data["filename"])

        # storing the page
        request.app.pages_db.set(url, {"html": data["text"]})
        v_payload = json.dumps({"url": url, "text": data["text"]})

        resp = build_vector(v_payload)

        # for some reason, running in a separate process blocks everything in docker
        # XXX to dig
        # try:
        #    resp = await request.app.run_in_executor(build_vector, v_payload)
        # except Exception as e:
        #    print(f"Failed to vectorize {repr(e)}")
        #    return await request.app.json_resp({"error": str(e)}, 400)

        resp = json.loads(resp)
        print("Vectorize")

        if "error" in resp:
            print(f"Failed to vectorize {resp['error']}")
            return await request.app.json_resp(resp, 400)

        vectors = resp["vectors"]
        sentences = resp["sentences"]
        title = resp["title"]

        if len(sentences) < 5:
            print(f"only {len(sentences)} skipping")
            return await request.app.json_resp(
                {"result": f"only {len(sentences)} skipping"}, 200
            )

        points = []

        for idx, (vec, sentence) in enumerate(zip(vectors, sentences, strict=True)):
            try:
                point = request.app.client.create_point(
                    idx, url, title, list(numpy.asfarray(vec)), sentence
                )
            except Exception as e:
                print("Failed to create a point")
                return await request.app.json_resp({"error": str(e)}, 400)

            points.append(point)

        try:
            resp = await request.app.client.index(points=points)
            resp = [json.loads(item) for item in resp]
            resp = {
                "backend_resp": resp,
                "message": f"Vectorized {len(sentences)} sentences",
            }
            res = await request.app.json_resp(resp)
        except Exception as e:
            print("Failed to send points to vector db")
            return await request.app.json_resp({"error": str(e)}, 400)

        await request.app.db.indexed(url)
        return res

    except Exception as e:
        return await request.app.json_resp(error_to_json(e), 400)


@apis.get("/remove_index")
async def remove_index(request):
    domain = request.rel_url.query["domain"]
    await request.app.db.set_skip(domain, True)
    # TODO: remove indexed content...
    raise web.HTTPFound("/admin")


@apis.get("/remove_skip")
async def remove_skip(request):
    domain = request.rel_url.query["domain"]
    await request.app.db.set_skip(domain, False)
    raise web.HTTPFound("/admin")


@apis.get("/domain_info")
async def info(request):
    url = request.rel_url.query["url"]
    res = await request.app.db.domain_info(url)
    return web.json_response(res)


@apis.get("/answer/{uuid}")
async def answer(request):
    uuid = request.match_info["uuid"]
    from places.web import ANSWERS

    start = time.time()
    while uuid not in ANSWERS and (time.time() - start < 30):
        await asyncio.sleep(0.1)

    task = ANSWERS.get(uuid)
    if task is None:
        return await request.app.json_resp(
            {"url": "url", "extract": "N/A", "answer": "Nothing found"}
        )

    if isinstance(task, dict):
        return await request.app.json_resp(task)

    await task

    if task.exception() is not None:
        raise task.exception()

    data = task.result()
    ANSWERS[uuid] = data

    return await request.app.json_resp(data)
