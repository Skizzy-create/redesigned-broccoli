from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    task_type: str
    payload: dict
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    result: dict | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
