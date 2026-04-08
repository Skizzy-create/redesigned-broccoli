import pytest

from app.queue.models import TaskStatus
from app.queue.task_queue import InMemoryTaskQueue, TaskNotFoundError, TaskQueueFullError


@pytest.mark.asyncio
async def test_enqueue_creates_pending_task():
    queue = InMemoryTaskQueue(max_pending=10)

    task = await queue.enqueue("noop", {"doc_id": "123"})
    stored = await queue.get_status(task.task_id)

    assert stored.task_id == task.task_id
    assert stored.task_type == "noop"
    assert stored.payload == {"doc_id": "123"}
    assert stored.status == TaskStatus.PENDING
    assert stored.progress == 0


@pytest.mark.asyncio
async def test_queue_full_raises_error():
    queue = InMemoryTaskQueue(max_pending=1)

    await queue.enqueue("noop", {})

    with pytest.raises(TaskQueueFullError):
        await queue.enqueue("noop", {})


@pytest.mark.asyncio
async def test_progress_is_bounded_between_zero_and_hundred():
    queue = InMemoryTaskQueue(max_pending=5)
    task = await queue.enqueue("noop", {})

    await queue.update_progress(task.task_id, -10)
    assert (await queue.get_status(task.task_id)).progress == 0

    await queue.update_progress(task.task_id, 500)
    assert (await queue.get_status(task.task_id)).progress == 100


@pytest.mark.asyncio
async def test_status_transitions_complete_and_cancel():
    queue = InMemoryTaskQueue(max_pending=5)
    first = await queue.enqueue("noop", {})
    second = await queue.enqueue("noop", {})

    await queue.mark_processing(first.task_id)
    await queue.mark_completed(first.task_id, result={"ok": True})

    completed = await queue.get_status(first.task_id)
    assert completed.status == TaskStatus.COMPLETED
    assert completed.progress == 100
    assert completed.result == {"ok": True}

    await queue.cancel(second.task_id)
    cancelled = await queue.get_status(second.task_id)
    assert cancelled.status == TaskStatus.FAILED
    assert cancelled.error == "Task cancelled by user."


@pytest.mark.asyncio
async def test_get_status_unknown_task_raises():
    queue = InMemoryTaskQueue(max_pending=1)

    with pytest.raises(TaskNotFoundError):
        await queue.get_status("missing-id")
