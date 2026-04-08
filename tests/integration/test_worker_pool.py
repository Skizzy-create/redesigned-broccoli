import asyncio

import pytest

from app.queue.models import TaskStatus
from app.queue.task_queue import InMemoryTaskQueue
from app.queue.worker_pool import WorkerPool


async def _wait_for_terminal_status(queue: InMemoryTaskQueue, task_id: str, timeout: float = 2.0):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        task = await queue.get_status(task_id)
        if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
            return task
        await asyncio.sleep(0.02)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


@pytest.mark.asyncio
async def test_worker_pool_processes_successful_task():
    queue = InMemoryTaskQueue(max_pending=5)

    async def success_handler(task_id: str, task_queue: InMemoryTaskQueue):
        await task_queue.update_progress(task_id, 25)
        await task_queue.update_progress(task_id, 75)
        return {"handled": True}

    pool = WorkerPool(task_queue=queue, handlers={"ingest": success_handler}, worker_count=1)
    await pool.start()

    task = await queue.enqueue("ingest", {"file": "a.pdf"})
    final = await _wait_for_terminal_status(queue, task.task_id)

    assert final.status == TaskStatus.COMPLETED
    assert final.result == {"handled": True}
    assert final.progress == 100

    await pool.stop()


@pytest.mark.asyncio
async def test_worker_pool_marks_unknown_task_type_as_failed():
    queue = InMemoryTaskQueue(max_pending=5)
    pool = WorkerPool(task_queue=queue, handlers={}, worker_count=1)
    await pool.start()

    task = await queue.enqueue("unknown-type", {})
    final = await _wait_for_terminal_status(queue, task.task_id)

    assert final.status == TaskStatus.FAILED
    assert "No handler registered" in (final.error or "")

    await pool.stop()


@pytest.mark.asyncio
async def test_worker_pool_marks_handler_exception_as_failed():
    queue = InMemoryTaskQueue(max_pending=5)

    async def failing_handler(task_id: str, task_queue: InMemoryTaskQueue):
        del task_id, task_queue
        raise RuntimeError("handler exploded")

    pool = WorkerPool(task_queue=queue, handlers={"ingest": failing_handler}, worker_count=1)
    await pool.start()

    task = await queue.enqueue("ingest", {})
    final = await _wait_for_terminal_status(queue, task.task_id)

    assert final.status == TaskStatus.FAILED
    assert "handler exploded" in (final.error or "")

    await pool.stop()
