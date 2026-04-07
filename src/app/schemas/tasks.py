from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TaskStatusData(BaseModel):
    task_id: str
    task_type: str
    status: str
    progress: int
    error: str | None
    result: dict | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
