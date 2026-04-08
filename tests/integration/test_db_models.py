import pytest
import pytest_asyncio
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import Conversation, Document, DocumentChunk, DocumentStatus, Message, MessageRole


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_document(db_session, checksum: str = "checksum-1") -> Document:
    document = Document(
        filename="sample.pdf",
        content_type="application/pdf",
        file_size=1024,
        checksum=checksum,
        status=DocumentStatus.PENDING,
        metadata_json={},
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


@pytest.mark.asyncio
async def test_can_persist_document_chunk_conversation_and_messages(db_session):
    document = await _create_document(db_session)

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="content",
        enriched_content="enriched",
        token_count=10,
        page_number=1,
        metadata_json={},
    )
    conversation = Conversation(document_id=document.id, summary="summary")
    user_message = Message(role=MessageRole.USER, content="Question", conversation=conversation)
    assistant_message = Message(role=MessageRole.ASSISTANT, content="Answer", conversation=conversation)

    db_session.add_all([chunk, conversation, user_message, assistant_message])
    await db_session.commit()

    chunk_count = await db_session.scalar(select(func.count()).select_from(DocumentChunk))
    conversation_count = await db_session.scalar(select(func.count()).select_from(Conversation))
    message_count = await db_session.scalar(select(func.count()).select_from(Message))

    assert chunk_count == 1
    assert conversation_count == 1
    assert message_count == 2


@pytest.mark.asyncio
async def test_document_checksum_must_be_unique(db_session):
    await _create_document(db_session, checksum="dup")

    duplicate = Document(
        filename="dup.pdf",
        content_type="application/pdf",
        file_size=100,
        checksum="dup",
        status=DocumentStatus.PENDING,
        metadata_json={},
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_chunk_index_must_be_unique_per_document(db_session):
    document = await _create_document(db_session, checksum="chunk-unique")

    first = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        content="first",
        token_count=10,
        metadata_json={},
    )
    second = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        content="second",
        token_count=12,
        metadata_json={},
    )

    db_session.add(first)
    await db_session.commit()

    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_cascade_delete_removes_related_rows(db_session):
    document = await _create_document(db_session, checksum="cascade")

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="chunk",
        token_count=8,
        metadata_json={},
    )
    conversation = Conversation(document_id=document.id)
    message = Message(role=MessageRole.USER, content="hello", conversation=conversation)

    db_session.add_all([chunk, conversation, message])
    await db_session.commit()

    await db_session.delete(document)
    await db_session.commit()

    document_count = await db_session.scalar(select(func.count()).select_from(Document))
    chunk_count = await db_session.scalar(select(func.count()).select_from(DocumentChunk))
    conversation_count = await db_session.scalar(select(func.count()).select_from(Conversation))
    message_count = await db_session.scalar(select(func.count()).select_from(Message))

    assert document_count == 0
    assert chunk_count == 0
    assert conversation_count == 0
    assert message_count == 0
