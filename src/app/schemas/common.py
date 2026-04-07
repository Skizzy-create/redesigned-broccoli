from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float | None = None


class SuccessResponse(BaseModel, Generic[T]):
    status: Literal["success"] = "success"
    data: T
    meta: Meta


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: ErrorDetails
    meta: Meta
