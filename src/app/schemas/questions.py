from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AskResponseData(BaseModel):
    answer: str
    conversation_id: str
    sources: list[dict]
    confidence: float
    retrieval_cycles: int
    status: str
    needs_more_context: bool = False
    clarifying_question: str | None = None
