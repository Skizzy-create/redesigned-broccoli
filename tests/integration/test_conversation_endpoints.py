import asyncio
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Document, DocumentStatus, Message, MessageRole
from app.db.session import get_session_factory


async def _seed_conversation() -> tuple[str, str]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        document = Document(
            filename="conv.pdf",
            content_type="application/pdf",
            file_size=100,
            checksum="conv-checksum",
            status=DocumentStatus.COMPLETED,
            chunk_count=1,
            metadata_json={"file_path": "data/uploads/conv.pdf"},
        )
        session.add(document)
        await session.flush()

        conversation = Conversation(document_id=document.id, summary="test summary")
        session.add(conversation)
        await session.flush()

        session.add_all(
            [
                Message(conversation_id=conversation.id, role=MessageRole.USER, content="Question"),
                Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Answer"),
            ]
        )
        await session.commit()
        return str(document.id), str(conversation.id)


def test_list_and_get_conversation(client, auth_headers):
    _, conversation_id = asyncio.run(_seed_conversation())

    listed = client.get("/api/v1/conversations", headers=auth_headers)
    assert listed.status_code == 200
    assert any(item["id"] == conversation_id for item in listed.json()["data"]["items"])

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["conversation"]["id"] == conversation_id
    assert len(detail.json()["data"]["messages"]) >= 2


def test_followup_ask_with_stubbed_qa_service(client, auth_headers, monkeypatch):
    _, conversation_id = asyncio.run(_seed_conversation())

    async def _stub_ask(session, *, document_id, question, conversation_id=None):
        del session, document_id, question
        return SimpleNamespace(
            answer="Follow-up answer",
            conversation_id=conversation_id,
            sources=[],
            confidence=0.77,
            retrieval_cycles=1,
            status="success",
            needs_more_context=False,
            clarifying_question=None,
        )

    monkeypatch.setattr(client.app.state.qa_service, "ask_document", _stub_ask)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/ask",
        headers=auth_headers,
        json={"question": "What about section two?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["answer"] == "Follow-up answer"
    assert payload["data"]["needs_more_context"] is False
    assert payload["data"]["clarifying_question"] is None


def test_delete_conversation(client, auth_headers):
    _, conversation_id = asyncio.run(_seed_conversation())

    delete_response = client.delete(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert get_response.status_code == 404
