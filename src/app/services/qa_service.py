from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Document, DocumentStatus, Message, MessageRole
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.provider import LLMProvider
from app.services.conversation_service import ConversationService
from app.services.retrieval_service import RetrievedChunk, RetrievalService


@dataclass(slots=True)
class QAResult:
    answer: str
    conversation_id: str
    sources: list[dict]
    confidence: float
    retrieval_cycles: int
    status: str
    needs_more_context: bool
    clarifying_question: str | None


class QAService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
    ) -> None:
        self._settings = get_settings()
        self._retrieval = retrieval_service
        self._conversations = conversation_service
        self._llm = llm_provider

    async def ask_document(
        self,
        session: AsyncSession,
        *,
        document_id: UUID,
        question: str,
        conversation_id: UUID | None = None,
    ) -> QAResult:
        document = await session.get(Document, document_id)
        if document is None:
            raise NotFoundError("Document not found.", code="document_not_found")
        if document.status != DocumentStatus.COMPLETED:
            raise ValidationError("Document is not ready for question answering.", code="document_not_ready")

        if conversation_id is None:
            conversation = await self._conversations.create_conversation(session, document_id=document_id)
        else:
            conversation = await self._conversations.get_conversation(session, conversation_id)

        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=question,
        )
        session.add(user_message)
        await session.commit()

        history = await self._conversations.get_messages(session, conversation.id, limit=8)
        rewritten_query = self._rewrite_followup(question=question, history=history)

        retrieval_cycles = 0
        retrieved: list[RetrievedChunk] = []
        confidence = 0.0
        active_query = rewritten_query

        for cycle in range(1, self._settings.rag_max_cycles + 1):
            retrieval_cycles = cycle
            retrieved = await self._retrieval.retrieve(session, document_id=document_id, query=active_query)
            confidence = self._confidence(retrieved)
            if retrieved and confidence >= self._settings.rag_min_confidence:
                break
            if cycle < self._settings.rag_max_cycles:
                active_query = self._refine_query(question=question, history=history, previous_query=active_query, retrieved=retrieved)

        sources = [
            {"chunk_id": chunk.chunk_id, "chunk_index": chunk.chunk_index, "score": round(chunk.score, 4)}
            for chunk in retrieved
        ]

        needs_more_context = False
        clarifying_question: str | None = None

        if not retrieved:
            clarifying_question = self._build_clarifying_question(question=question, reason="no_context")
            answer = clarifying_question
            status = "needs_more_context"
            needs_more_context = True
            confidence = 0.0
        elif confidence < self._settings.rag_min_confidence:
            clarifying_question = self._build_clarifying_question(question=question, reason="low_confidence")
            answer = (
                f"{clarifying_question}\n\n"
                "I found related passages, but not enough evidence to answer confidently yet."
            )
            status = "needs_more_context"
            needs_more_context = True
        else:
            context = self._build_context(retrieved)
            conversation_context = self._history_context(history)
            prompt = build_user_prompt(question=question, context=context, conversation_context=conversation_context)
            try:
                answer = await self._llm.generate(system_prompt=SYSTEM_PROMPT, user_prompt=prompt)
                status = "success"
            except Exception:
                answer = self._fallback_answer(retrieved)
                status = "partial"

        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            sources={"items": sources},
            confidence=confidence,
            model_used=None,
        )
        session.add(assistant_message)
        await session.commit()

        return QAResult(
            answer=answer,
            conversation_id=str(conversation.id),
            sources=sources,
            confidence=confidence,
            retrieval_cycles=retrieval_cycles,
            status=status,
            needs_more_context=needs_more_context,
            clarifying_question=clarifying_question,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        ordered = sorted(chunks, key=lambda item: item.chunk_index)
        sections: list[str] = []
        for chunk in ordered:
            sections.append(f"[Source chunk={chunk.chunk_index}] {chunk.content}")
        return "\n\n".join(sections)

    @staticmethod
    def _rewrite_followup(question: str, history: list[Message]) -> str:
        normalized = question.strip()
        if len(normalized.split()) >= 6:
            return normalized

        previous_user_questions = [msg.content for msg in history if msg.role == MessageRole.USER and msg.content.strip()]
        if not previous_user_questions:
            return normalized
        anchor = previous_user_questions[-1]
        return f"{anchor}. Follow-up: {normalized}"

    @staticmethod
    def _refine_query(question: str, history: list[Message], previous_query: str, retrieved: list[RetrievedChunk]) -> str:
        user_questions = [msg.content for msg in history if msg.role == MessageRole.USER and msg.content.strip()]
        history_anchor = " ".join(user_questions[-2:]) if user_questions else question
        if not retrieved:
            return (
                f"{previous_query}. Clarify entities, dates, and section titles for this request: {question}. "
                f"Conversation anchor: {history_anchor}."
            )

        hint_snippets = " ".join(" ".join(chunk.content.split()[:16]) for chunk in retrieved[:2])
        return (
            f"{previous_query}. Refine retrieval for: {question}. "
            f"Focus on exact terms and section matches. Candidate hints: {hint_snippets}"
        )

    @staticmethod
    def _history_context(history: list[Message]) -> str | None:
        if not history:
            return None
        lines = [f"{msg.role}: {msg.content}" for msg in history[-4:]]
        return "\n".join(lines)

    @staticmethod
    def _fallback_answer(chunks: list[RetrievedChunk]) -> str:
        top = sorted(chunks, key=lambda item: item.score, reverse=True)[:2]
        snippets = "\n".join(f"- {chunk.content[:240]}" for chunk in top)
        return (
            "The language model is currently unavailable. "
            "Here are the most relevant passages retrieved from the document:\n"
            f"{snippets}"
        )

    @staticmethod
    def _confidence(chunks: list[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0
        avg = sum(chunk.score for chunk in chunks) / len(chunks)
        bounded = max(0.0, min(1.0, (avg + 1) / 2))
        return round(bounded, 3)

    @staticmethod
    def _build_clarifying_question(question: str, reason: str) -> str:
        if reason == "no_context":
            return (
                "I could not find enough relevant context in the current retrieval pass. "
                "Could you provide one or more exact keywords, section names, or a short quote related to your question?"
            )

        return (
            f"I need a bit more context to answer confidently for: '{question}'. "
            "Could you narrow the scope (specific section, timeframe, entity, or policy name)?"
        )
