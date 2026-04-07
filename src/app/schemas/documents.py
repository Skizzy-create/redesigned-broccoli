from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentUploadData(BaseModel):
    document_id: str
    task_id: str
    status: Literal["queued"] = "queued"
    message: str


class DocumentData(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None


class DocumentListData(BaseModel):
    items: list[DocumentData]
