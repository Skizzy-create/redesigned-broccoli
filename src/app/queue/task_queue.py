import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.core.exceptions import NotFoundError, TooManyRequestsError
from app.queue.models import TaskRecord, TaskStatus


class TaskQueueFullError(TooManyRequestsError):
    def __init__(self, message: str = "Task queue is full.") -> None:
        super().__init__(message=message, code="task_queue_full")


class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: str) -> None:
        super().__init__(message=f"Task '{task_id}' was not found.", code="task_not_found")


class InMemoryTaskQueue:
    def __init__(self, max_pending: int = 1000) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=max_pending)
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()

    async def enqueue(self, task_type: str, payload: dict) -> TaskRecord:
        task_id = str(uuid4())
        task = TaskRecord(task_id=task_id, task_type=task_type, payload=payload)

        async with self._lock:
            if self._queue.full():
                raise TaskQueueFullError("Task queue is full.")
            self._tasks[task_id] = task
            self._queue.put_nowait(task_id)

        return task

    async def next_task_id(self, timeout_seconds: float = 0.5) -> str:
        return await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)

    def task_done(self) -> None:
        self._queue.task_done()

    async def get_status(self, task_id: str) -> TaskRecord:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskNotFoundError(task_id)
            return task

    async def mark_processing(self, task_id: str) -> None:
        async with self._lock:
            task = self._get_task_or_raise(task_id)
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(timezone.utc)
            task.error = None

    async def update_progress(self, task_id: str, progress: int) -> None:
        bounded_progress = max(0, min(progress, 100))
        async with self._lock:
            task = self._get_task_or_raise(task_id)
            task.progress = bounded_progress

    async def mark_completed(self, task_id: str, result: dict | None = None) -> None:
        async with self._lock:
            task = self._get_task_or_raise(task_id)
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            task.error = None

    async def mark_failed(self, task_id: str, error: str) -> None:
        async with self._lock:
            task = self._get_task_or_raise(task_id)
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now(timezone.utc)

    async def cancel(self, task_id: str) -> None:
        await self.mark_failed(task_id, "Task cancelled by user.")

    async def pending_count(self) -> int:
        return self._queue.qsize()

    def _get_task_or_raise(self, task_id: str) -> TaskRecord:
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
