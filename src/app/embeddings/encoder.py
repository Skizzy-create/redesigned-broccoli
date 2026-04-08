# pyright: reportMissingImports=false

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Sequence

from app.core.exceptions import ServiceUnavailableError


class EmbeddingEncoder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @lru_cache
    def _model(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ServiceUnavailableError("sentence-transformers is not installed.", code="embedding_model_unavailable") from exc

        return SentenceTransformer(self._model_name)

    async def encode(self, texts: Sequence[str]) -> Any:
        if not texts:
            import numpy as np

            return np.zeros((0, 0), dtype=np.float32)

        return await asyncio.to_thread(self._encode_sync, list(texts))

    def _encode_sync(self, texts: list[str]) -> Any:
        import numpy as np

        vectors = self._model().encode(texts, batch_size=64, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @lru_cache
    def _model(self):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ServiceUnavailableError("sentence-transformers is not installed.", code="reranker_unavailable") from exc

        return CrossEncoder(self._model_name)

    async def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []

        pairs = [(query, passage) for passage in passages]
        values = await asyncio.to_thread(self._model().predict, pairs)
        return [float(v) for v in values]
