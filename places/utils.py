import functools
import asyncio
from contextlib import asynccontextmanager


class Tasks:
    def __init__(self, concurrency=5, cb=None):
        self.concurrency = concurrency
        self.tasks = []
        self.cb = cb
        self._done = asyncio.Event()

    def _callback(self, task, cb=None):
        self.tasks.remove(task)
        self._done.set()
        if task.exception():
            print(f"Exception found for task {task.get_name()}: {task.exception()}")
        if cb is not None:
            cb(task.result())
        if self.cb is not None:
            self.cb(task.result())

    async def put(self, coroutine, cb=None):
        if len(self.tasks) >= self.concurrency:
            await self._done.wait()
            self._done.clear()
        task = asyncio.create_task(coroutine())
        self.tasks.append(task)
        task.add_done_callback(functools.partial(self._callback, cb=cb))
        return task

    async def join(self):
        await asyncio.gather(*self.tasks, return_exceptions=True)

    def cancel(self):
        for task in self.tasks:
            task.cancel()


@asynccontextmanager
async def task_pool(max_tasks=10, cb=None):
    tasks = Tasks(max_tasks, cb)
    try:
        yield tasks
    finally:
        await tasks.join()
