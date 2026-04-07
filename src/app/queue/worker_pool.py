import asyncio
from collections.abc import Awaitable, Callable

from app.queue.task_queue import InMemoryTaskQueue

TaskHandler = Callable[[str, InMemoryTaskQueue], Awaitable[dict | None]]


class WorkerPool:
    def __init__(
        self,
        task_queue: InMemoryTaskQueue,
        handlers: dict[str, TaskHandler],
        worker_count: int = 4,
    ) -> None:
        self._task_queue = task_queue
        self._handlers = handlers
        self._worker_count = worker_count
        self._workers: list[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._workers:
            return

        self._stop_event.clear()
        self._workers = [
            asyncio.create_task(self._worker_loop(index), name=f"task-worker-{index}")
            for index in range(self._worker_count)
        ]

    async def stop(self) -> None:
        if not self._workers:
            return

        self._stop_event.set()
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def _worker_loop(self, worker_index: int) -> None:
        del worker_index
        while not self._stop_event.is_set():
            try:
                task_id = await self._task_queue.next_task_id(timeout_seconds=0.5)
            except asyncio.TimeoutError:
                continue

            try:
                task = await self._task_queue.get_status(task_id)
                handler = self._handlers.get(task.task_type)
                await self._task_queue.mark_processing(task_id)

                if handler is None:
                    await self._task_queue.mark_failed(task_id, f"No handler registered for '{task.task_type}'.")
                else:
                    result = await handler(task_id, self._task_queue)
                    await self._task_queue.mark_completed(task_id, result=result)
            except Exception as exc:  # noqa: BLE001
                await self._task_queue.mark_failed(task_id, str(exc))
            finally:
                self._task_queue.task_done()
