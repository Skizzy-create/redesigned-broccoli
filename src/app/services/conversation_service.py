from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Conversation, Message


class ConversationService:
    async def create_conversation(self, session: AsyncSession, document_id: UUID) -> Conversation:
        conversation = Conversation(document_id=document_id)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation

    async def get_conversation(self, session: AsyncSession, conversation_id: UUID) -> Conversation:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found.", code="conversation_not_found")
        return conversation

    async def list_conversations(self, session: AsyncSession) -> list[Conversation]:
        rows = await session.scalars(select(Conversation).order_by(Conversation.updated_at.desc()))
        return list(rows)

    async def get_messages(self, session: AsyncSession, conversation_id: UUID, limit: int | None = None) -> list[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        if limit is not None:
            query = query.limit(limit)
        rows = await session.scalars(query)
        return list(rows)
