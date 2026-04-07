from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from celery.result import AsyncResult

from app.dependencies import get_celery_app
from app.schemas.common import Meta, SuccessResponse
from app.schemas.tasks import TaskStatusData

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _meta(request: Request) -> Meta:
    return Meta(request_id=getattr(request.state, "request_id", "unknown"))


@router.get("/{task_id}", response_model=SuccessResponse[TaskStatusData])
async def get_task_status(request: Request, task_id: str, celery_app=Depends(get_celery_app)) -> SuccessResponse[TaskStatusData]:
    task = AsyncResult(task_id, app=celery_app)

    state = (task.state or "PENDING").upper()
    meta = task.info if isinstance(task.info, dict) else {}
    status_map = {
        "PENDING": "pending",
        "RECEIVED": "processing",
        "STARTED": "processing",
        "PROGRESS": "processing",
        "RETRY": "processing",
        "SUCCESS": "completed",
        "FAILURE": "failed",
        "REVOKED": "failed",
    }

    status_value = status_map.get(state, "pending")
    progress = int(meta.get("progress", 0)) if isinstance(meta, dict) else 0
    if status_value == "completed":
        progress = 100

    created_at = datetime.now(timezone.utc)
    started_at = meta.get("started_at") if isinstance(meta, dict) else None
    completed_at = meta.get("completed_at") if isinstance(meta, dict) else None
    result_payload = task.result if status_value == "completed" and isinstance(task.result, dict) else None
    error_payload = None
    if status_value == "failed":
        error_payload = str(task.result)

    payload = TaskStatusData(
        task_id=task_id,
        task_type=meta.get("task_type", "ingest_document"),
        status=status_value,
        progress=progress,
        error=error_payload,
        result=result_payload,
        created_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
    )
    return SuccessResponse(data=payload, meta=_meta(request))
