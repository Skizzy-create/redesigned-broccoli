from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MessageRole
from app.db.session import get_async_session
from app.dependencies import get_conversation_service, get_qa_service
from app.schemas.common import Meta, SuccessResponse
from app.schemas.conversations import ConversationData, ConversationDetailData, ConversationListData, MessageData
from app.schemas.questions import AskRequest, AskResponseData

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def _meta(request: Request) -> Meta:
    return Meta(request_id=getattr(request.state, "request_id", "unknown"))


def _to_conversation_data(conversation) -> ConversationData:
    return ConversationData(
        id=str(conversation.id),
        document_id=str(conversation.document_id),
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _to_message_data(message) -> MessageData:
    return MessageData(
        id=str(message.id),
        role=message.role.value if isinstance(message.role, MessageRole) else str(message.role),
        content=message.content,
        sources=message.sources,
        confidence=message.confidence,
        created_at=message.created_at,
    )


@router.post("/{conversation_id}/ask", response_model=SuccessResponse[AskResponseData])
async def ask_followup(
    request: Request,
    conversation_id: UUID,
    body: AskRequest,
    session: AsyncSession = Depends(get_async_session),
    qa_service=Depends(get_qa_service),
    conversation_service=Depends(get_conversation_service),
) -> SuccessResponse[AskResponseData]:
    conversation = await conversation_service.get_conversation(session, conversation_id)
    result = await qa_service.ask_document(
        session,
        document_id=conversation.document_id,
        question=body.question,
        conversation_id=conversation_id,
    )
    payload = AskResponseData(
        answer=result.answer,
        conversation_id=str(result.conversation_id),
        sources=result.sources,
        confidence=result.confidence,
        retrieval_cycles=result.retrieval_cycles,
        status=result.status,
        needs_more_context=getattr(result, "needs_more_context", False),
        clarifying_question=getattr(result, "clarifying_question", None),
    )
    return SuccessResponse(data=payload, meta=_meta(request))


@router.get("", response_model=SuccessResponse[ConversationListData])
async def list_conversations(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    conversation_service=Depends(get_conversation_service),
) -> SuccessResponse[ConversationListData]:
    conversations = await conversation_service.list_conversations(session)
    return SuccessResponse(
        data=ConversationListData(items=[_to_conversation_data(item) for item in conversations]),
        meta=_meta(request),
    )


@router.get("/{conversation_id}", response_model=SuccessResponse[ConversationDetailData])
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    conversation_service=Depends(get_conversation_service),
) -> SuccessResponse[ConversationDetailData]:
    conversation = await conversation_service.get_conversation(session, conversation_id)
    messages = await conversation_service.get_messages(session, conversation_id)

    payload = ConversationDetailData(
        conversation=_to_conversation_data(conversation),
        messages=[_to_message_data(item) for item in messages],
    )
    return SuccessResponse(data=payload, meta=_meta(request))


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    conversation_service=Depends(get_conversation_service),
):
    conversation = await conversation_service.get_conversation(session, conversation_id)
    await session.delete(conversation)
    await session.commit()
    return None
