from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MessageData(BaseModel):
    id: str
    role: str
    content: str
    sources: dict | None
    confidence: float | None
    created_at: datetime


class ConversationData(BaseModel):
    id: str
    document_id: str
    summary: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailData(BaseModel):
    conversation: ConversationData
    messages: list[MessageData]


class ConversationListData(BaseModel):
    items: list[ConversationData]
