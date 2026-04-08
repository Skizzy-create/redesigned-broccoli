from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import DocumentStatus, MessageRole
from app.services.qa_service import QAService
from app.services.retrieval_service import RetrievedChunk


class FakeSession:
    def __init__(self, document):
        self._document = document
        self.added: list[object] = []
        self.commit_count = 0

    async def get(self, _model, _document_id):
        return self._document

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commit_count += 1


class FakeConversationService:
    def __init__(self, history: list[object] | None = None):
        self._history = history or []
        self._conversation_id = uuid4()

    async def create_conversation(self, _session, document_id):
        return SimpleNamespace(id=self._conversation_id, document_id=document_id)

    async def get_conversation(self, _session, conversation_id):
        return SimpleNamespace(id=conversation_id, document_id=uuid4())

    async def get_messages(self, _session, _conversation_id, limit=None):
        if limit is None:
            return self._history
        return self._history[-limit:]


class FakeRetrievalService:
    def __init__(self, responses: list[list[RetrievedChunk]]):
        self._responses = responses
        self.calls: list[str] = []

    async def retrieve(self, _session, document_id, query):
        del document_id
        self.calls.append(query)
        index = min(len(self.calls) - 1, len(self._responses) - 1)
        return self._responses[index]


class FakeLLMProvider:
    def __init__(self, response: str = "ok", should_raise: bool = False):
        self._response = response
        self._should_raise = should_raise
        self.call_count = 0

    async def generate(self, system_prompt: str, user_prompt: str):
        del system_prompt, user_prompt
        self.call_count += 1
        if self._should_raise:
            raise RuntimeError("llm unavailable")
        return self._response


def _doc(status: DocumentStatus):
    return SimpleNamespace(id=uuid4(), status=status)


def _history(*questions: str):
    return [SimpleNamespace(role=MessageRole.USER, content=q) for q in questions]


@pytest.mark.asyncio
async def test_ask_document_raises_when_document_missing():
    service = QAService(
        retrieval_service=FakeRetrievalService([[]]),
        conversation_service=FakeConversationService(),
        llm_provider=FakeLLMProvider(),
    )
    session = FakeSession(document=None)

    with pytest.raises(NotFoundError):
        await service.ask_document(session, document_id=uuid4(), question="What is this?")


@pytest.mark.asyncio
async def test_ask_document_raises_when_document_not_ready():
    service = QAService(
        retrieval_service=FakeRetrievalService([[]]),
        conversation_service=FakeConversationService(),
        llm_provider=FakeLLMProvider(),
    )
    session = FakeSession(document=_doc(DocumentStatus.PROCESSING))

    with pytest.raises(ValidationError):
        await service.ask_document(session, document_id=uuid4(), question="What is this?")


@pytest.mark.asyncio
async def test_ask_document_requests_more_context_when_no_chunks_found():
    retrieval = FakeRetrievalService([[], []])
    llm = FakeLLMProvider()
    service = QAService(
        retrieval_service=retrieval,
        conversation_service=FakeConversationService(history=_history("Where is the policy section?")),
        llm_provider=llm,
    )
    session = FakeSession(document=_doc(DocumentStatus.COMPLETED))

    result = await service.ask_document(session, document_id=uuid4(), question="What about it?")

    assert result.status == "needs_more_context"
    assert result.needs_more_context is True
    assert result.clarifying_question is not None
    assert result.retrieval_cycles == 2
    assert result.sources == []
    assert llm.call_count == 0
    assert len(retrieval.calls) == 2


@pytest.mark.asyncio
async def test_ask_document_requests_more_context_when_confidence_low():
    low_chunk = RetrievedChunk(chunk_id=str(uuid4()), content="generic text", chunk_index=0, score=-0.8)
    retrieval = FakeRetrievalService([[low_chunk], [low_chunk]])
    llm = FakeLLMProvider()
    service = QAService(
        retrieval_service=retrieval,
        conversation_service=FakeConversationService(history=_history("Tell me details")),
        llm_provider=llm,
    )
    session = FakeSession(document=_doc(DocumentStatus.COMPLETED))

    result = await service.ask_document(session, document_id=uuid4(), question="details?")

    assert result.status == "needs_more_context"
    assert result.needs_more_context is True
    assert result.clarifying_question is not None
    assert result.retrieval_cycles == 2
    assert len(result.sources) == 1
    assert llm.call_count == 0


@pytest.mark.asyncio
async def test_ask_document_returns_success_when_confidence_high():
    high_chunk = RetrievedChunk(chunk_id=str(uuid4()), content="policy says x", chunk_index=1, score=0.95)
    retrieval = FakeRetrievalService([[high_chunk]])
    llm = FakeLLMProvider(response="ANSWER: policy says x\nSOURCES: [Source chunk=1]")
    service = QAService(
        retrieval_service=retrieval,
        conversation_service=FakeConversationService(history=_history("Policy question")),
        llm_provider=llm,
    )
    session = FakeSession(document=_doc(DocumentStatus.COMPLETED))

    result = await service.ask_document(session, document_id=uuid4(), question="What does policy say?")

    assert result.status == "success"
    assert result.needs_more_context is False
    assert result.clarifying_question is None
    assert result.retrieval_cycles == 1
    assert result.confidence >= 0.55
    assert llm.call_count == 1


@pytest.mark.asyncio
async def test_ask_document_returns_partial_when_llm_fails():
    high_chunk = RetrievedChunk(chunk_id=str(uuid4()), content="policy says x", chunk_index=1, score=0.95)
    retrieval = FakeRetrievalService([[high_chunk]])
    llm = FakeLLMProvider(should_raise=True)
    service = QAService(
        retrieval_service=retrieval,
        conversation_service=FakeConversationService(history=_history("Policy question")),
        llm_provider=llm,
    )
    session = FakeSession(document=_doc(DocumentStatus.COMPLETED))

    result = await service.ask_document(session, document_id=uuid4(), question="What does policy say?")

    assert result.status == "partial"
    assert "language model is currently unavailable" in result.answer.lower()
    assert result.needs_more_context is False
    assert result.retrieval_cycles == 1
