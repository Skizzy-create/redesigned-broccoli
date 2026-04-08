# pyright: reportMissingImports=false

from __future__ import annotations

from dataclasses import dataclass

from app.processing.parsers.base import ParsedDocument


@dataclass(slots=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    metadata: dict


def _count_tokens(text: str) -> int:
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text.split())


def _split_recursive(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    if not text.strip():
        return []

    words = text.split()
    if len(words) <= target_tokens:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    stride = max(1, target_tokens - overlap_tokens)
    while start < len(words):
        end = min(len(words), start + target_tokens)
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += stride

    return chunks


def chunk_document(parsed: ParsedDocument, chunk_size_tokens: int, overlap_tokens: int) -> list[TextChunk]:
    paragraphs = [p.strip() for p in parsed.text.split("\n\n") if p and p.strip()]
    joined = "\n\n".join(paragraphs)
    raw_chunks = _split_recursive(joined, target_tokens=chunk_size_tokens, overlap_tokens=overlap_tokens)

    chunks: list[TextChunk] = []
    for index, raw in enumerate(raw_chunks):
        chunks.append(
            TextChunk(
                chunk_index=index,
                content=raw,
                token_count=_count_tokens(raw),
                metadata={"page_count": parsed.page_count},
            )
        )

    return chunks
