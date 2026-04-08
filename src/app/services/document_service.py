from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models import Document
from app.vectorstore.faiss_store import FaissStore


class DocumentService:
    def __init__(self, faiss_store: FaissStore) -> None:
        self._faiss_store = faiss_store

    @staticmethod
    def checksum_from_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def create_document(
        self,
        session: AsyncSession,
        *,
        filename: str,
        content_type: str,
        file_size: int,
        checksum: str,
        file_path: str,
    ) -> Document:
        existing = await session.scalar(select(Document).where(Document.checksum == checksum))
        if existing is not None:
            raise ConflictError(message="Document with same checksum already exists.", code="duplicate_document")

        document = Document(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            checksum=checksum,
            metadata_json={"file_path": file_path},
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    async def list_documents(self, session: AsyncSession) -> list[Document]:
        rows = await session.scalars(select(Document).order_by(Document.created_at.desc()))
        return list(rows)

    async def get_document(self, session: AsyncSession, document_id: UUID) -> Document:
        document = await session.get(Document, document_id)
        if document is None:
            raise NotFoundError(message="Document not found.", code="document_not_found")
        return document

    async def delete_document(self, session: AsyncSession, document_id: UUID) -> None:
        document = await self.get_document(session, document_id)
        file_path = (document.metadata_json or {}).get("file_path")

        await session.delete(document)
        await session.commit()

        if file_path:
            path = Path(file_path)
            if path.exists():
                path.unlink(missing_ok=True)

        self._faiss_store.delete_document_index(str(document_id))
