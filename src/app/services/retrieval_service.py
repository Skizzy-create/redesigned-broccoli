from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import DocumentChunk
from app.embeddings.encoder import CrossEncoderReranker, EmbeddingEncoder
from app.vectorstore.faiss_store import FaissStore


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    chunk_index: int
    score: float


class RetrievalService:
    def __init__(self, encoder: EmbeddingEncoder, reranker: CrossEncoderReranker, faiss_store: FaissStore) -> None:
        self._settings = get_settings()
        self._encoder = encoder
        self._reranker = reranker
        self._faiss_store = faiss_store

    async def retrieve(self, session: AsyncSession, document_id: UUID, query: str) -> list[RetrievedChunk]:
        query_vector = await self._encoder.encode([query])
        semantic = self._faiss_store.semantic_search(str(document_id), query_vector, self._settings.top_k_retrieval)
        lexical = self._faiss_store.bm25_search(str(document_id), query, self._settings.top_k_retrieval)

        fused_scores: dict[str, float] = {}
        for rank, match in enumerate(semantic, start=1):
            fused_scores[match.chunk_id] = fused_scores.get(match.chunk_id, 0.0) + 1.0 / (60 + rank)
        for rank, match in enumerate(lexical, start=1):
            fused_scores[match.chunk_id] = fused_scores.get(match.chunk_id, 0.0) + 1.0 / (60 + rank)

        if not fused_scores:
            return []

        sorted_chunk_ids = [chunk_id for chunk_id, _ in sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)]
        chunk_uuid_map = {UUID(chunk_id): chunk_id for chunk_id in sorted_chunk_ids}

        rows = await session.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(list(chunk_uuid_map.keys()))))
        chunk_map = {str(chunk.id): chunk for chunk in rows}

        ordered = [chunk_map[chunk_id] for chunk_id in sorted_chunk_ids if chunk_id in chunk_map]
        rerank_scores: list[float] = []
        try:
            rerank_scores = await self._reranker.score(query=query, passages=[chunk.content for chunk in ordered])
        except Exception:
            rerank_scores = [fused_scores[str(chunk.id)] for chunk in ordered]

        combined = [
            RetrievedChunk(
                chunk_id=str(chunk.id),
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                score=float(rerank_scores[index]),
            )
            for index, chunk in enumerate(ordered)
        ]
        combined.sort(key=lambda item: item.score, reverse=True)
        return combined[: self._settings.top_n_rerank]
