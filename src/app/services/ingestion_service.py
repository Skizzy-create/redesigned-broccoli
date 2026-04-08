from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.core.exceptions import DocumentProcessingError
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.embeddings.encoder import EmbeddingEncoder
from app.processing.chunking.strategies import chunk_document
from app.processing.parsers.factory import DocumentParserFactory
from app.vectorstore.faiss_store import FaissStore


class IngestionService:
    def __init__(self, encoder: EmbeddingEncoder, faiss_store: FaissStore) -> None:
        self._settings = get_settings()
        self._encoder = encoder
        self._faiss_store = faiss_store

    async def ingest_document(
        self,
        *,
        session_factory: async_sessionmaker,
        document_id: str,
        file_path: str,
        content_type: str,
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict:
        def _notify_progress(progress: int) -> None:
            if progress_callback is None:
                return
            progress_callback(progress)

        async with session_factory() as session:
            document = await session.get(Document, UUID(document_id))
            if document is None:
                raise DocumentProcessingError("Document not found during ingestion.", code="document_not_found")

            try:
                document.status = DocumentStatus.PROCESSING
                document.error_message = None
                await session.commit()

                _notify_progress(5)
                parser = DocumentParserFactory.from_file(content_type=content_type, filename=document.filename)
                parsed = await asyncio.to_thread(parser.parse, Path(file_path))

                if not parsed.text.strip():
                    raise DocumentProcessingError("No extractable text content.", code="empty_document")

                _notify_progress(25)
                chunks = chunk_document(
                    parsed=parsed,
                    chunk_size_tokens=self._settings.chunk_size_tokens,
                    overlap_tokens=self._settings.chunk_overlap_tokens,
                )
                if not chunks:
                    raise DocumentProcessingError("No chunks generated.", code="chunking_failed")

                _notify_progress(45)
                vectors = await self._encoder.encode([chunk.content for chunk in chunks])
                _notify_progress(65)

                await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
                session.add_all(
                    [
                        DocumentChunk(
                            document_id=document.id,
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                            enriched_content=None,
                            token_count=chunk.token_count,
                            page_number=None,
                            embedding=vectors[index].astype("float32").tobytes(),
                            metadata_json=chunk.metadata,
                        )
                        for index, chunk in enumerate(chunks)
                    ]
                )
                await session.commit()
                _notify_progress(80)

                persisted_chunks = list(
                    await session.scalars(
                        select(DocumentChunk)
                        .where(DocumentChunk.document_id == document.id)
                        .order_by(DocumentChunk.chunk_index)
                    )
                )
                chunk_ids = [str(chunk.id) for chunk in persisted_chunks]
                chunk_texts = [chunk.content for chunk in persisted_chunks]

                self._faiss_store.persist_document_index(
                    document_id=document_id,
                    vectors=vectors,
                    chunk_ids=chunk_ids,
                    chunk_texts=chunk_texts,
                )

                document.chunk_count = len(chunks)
                document.status = DocumentStatus.COMPLETED
                document.processed_at = datetime.now(timezone.utc)
                document.metadata_json = {
                    **(document.metadata_json or {}),
                    "page_count": parsed.page_count,
                    "parser_metadata": parsed.metadata,
                }
                await session.commit()
                _notify_progress(100)
                return {"document_id": document_id, "chunk_count": len(chunks)}
            except Exception as exc:  # noqa: BLE001
                document.status = DocumentStatus.FAILED
                document.error_message = str(exc)
                await session.commit()
                raise
