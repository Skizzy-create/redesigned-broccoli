# pyright: reportMissingImports=false

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SemanticMatch:
    chunk_id: str
    score: float


class FaissStore:
    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def _doc_dir(self, document_id: str) -> Path:
        path = self._root / f"doc_{document_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def persist_document_index(
        self,
        document_id: str,
        vectors,
        chunk_ids: list[str],
        chunk_texts: list[str],
    ) -> None:
        import numpy as np

        doc_dir = self._doc_dir(document_id)
        np.save(doc_dir / "vectors.npy", vectors)
        metadata = {"chunk_ids": chunk_ids, "chunk_texts": chunk_texts}
        (doc_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        try:
            import faiss

            if vectors.size == 0:
                return

            dim = int(vectors.shape[1])
            index = faiss.IndexFlatIP(dim)
            index.add(vectors)
            faiss.write_index(index, str(doc_dir / "index.faiss"))
        except Exception:
            # Fallback to numpy search when faiss is unavailable.
            return

    def semantic_search(self, document_id: str, query_vector, top_k: int) -> list[SemanticMatch]:
        import numpy as np

        doc_dir = self._doc_dir(document_id)
        metadata_path = doc_dir / "metadata.json"
        if not metadata_path.exists():
            return []

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunk_ids: list[str] = metadata["chunk_ids"]

        index_path = doc_dir / "index.faiss"
        if index_path.exists():
            try:
                import faiss

                index = faiss.read_index(str(index_path))
                scores, indices = index.search(query_vector.astype(np.float32), top_k)
                output: list[SemanticMatch] = []
                for rank, idx in enumerate(indices[0].tolist()):
                    if idx < 0 or idx >= len(chunk_ids):
                        continue
                    output.append(SemanticMatch(chunk_id=chunk_ids[idx], score=float(scores[0][rank])))
                return output
            except Exception:
                pass

        vectors = np.load(doc_dir / "vectors.npy")
        scores = np.dot(vectors, query_vector[0])
        top_indices = np.argsort(-scores)[:top_k]
        return [SemanticMatch(chunk_id=chunk_ids[i], score=float(scores[i])) for i in top_indices]

    def bm25_search(self, document_id: str, query: str, top_k: int) -> list[SemanticMatch]:
        import numpy as np

        doc_dir = self._doc_dir(document_id)
        metadata_path = doc_dir / "metadata.json"
        if not metadata_path.exists():
            return []

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunk_ids: list[str] = metadata["chunk_ids"]
        chunk_texts: list[str] = metadata["chunk_texts"]

        try:
            from rank_bm25 import BM25Okapi

            corpus = [text.lower().split() for text in chunk_texts]
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(query.lower().split())
            top_indices = np.argsort(-scores)[:top_k]
            return [SemanticMatch(chunk_id=chunk_ids[i], score=float(scores[i])) for i in top_indices]
        except Exception:
            query_tokens = set(query.lower().split())
            if not query_tokens:
                return []

            scored: list[tuple[int, float]] = []
            for idx, text in enumerate(chunk_texts):
                tokens = set(text.lower().split())
                overlap = len(query_tokens.intersection(tokens))
                if overlap > 0:
                    scored.append((idx, float(overlap)))

            scored.sort(key=lambda item: item[1], reverse=True)
            return [SemanticMatch(chunk_id=chunk_ids[idx], score=score) for idx, score in scored[:top_k]]

    def delete_document_index(self, document_id: str) -> None:
        doc_dir = self._root / f"doc_{document_id}"
        if not doc_dir.exists():
            return

        for child in doc_dir.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        doc_dir.rmdir()
