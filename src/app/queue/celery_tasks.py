from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.db.session import get_session_factory
from app.embeddings.encoder import EmbeddingEncoder
from app.processing.parsers.factory import DocumentParserFactory
from app.queue.celery_app import celery_app
from app.services.ingestion_service import IngestionService
from app.vectorstore.faiss_store import FaissStore
from app.config import get_settings


def _build_ingestion_service() -> IngestionService:
    settings = get_settings()
    encoder = EmbeddingEncoder(settings.embedding_model)
    faiss_store = FaissStore(settings.index_dir)
    return IngestionService(encoder=encoder, faiss_store=faiss_store)


@celery_app.task(bind=True, name="app.queue.ingest_document")
def ingest_document_task(self, document_id: str, file_path: str, content_type: str) -> dict:
    settings = get_settings()
    DocumentParserFactory.from_file(content_type=content_type, filename=file_path)

    started_at = datetime.now(timezone.utc).isoformat()
    self.update_state(
        state="STARTED",
        meta={
            "task_type": "ingest_document",
            "progress": 1,
            "started_at": started_at,
        },
    )

    def progress_callback(progress: int) -> None:
        self.update_state(
            state="PROGRESS",
            meta={
                "task_type": "ingest_document",
                "progress": progress,
                "started_at": started_at,
            },
        )

    async def _run() -> dict:
        service = _build_ingestion_service()
        session_factory = get_session_factory()
        result = await service.ingest_document(
            session_factory=session_factory,
            document_id=document_id,
            file_path=file_path,
            content_type=content_type,
            progress_callback=progress_callback,
        )
        return {
            **result,
            "task_type": "ingest_document",
            "progress": 100,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "worker_count": settings.max_workers,
        }

    return asyncio.run(_run())
