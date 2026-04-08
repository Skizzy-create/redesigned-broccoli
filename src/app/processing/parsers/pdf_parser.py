# pyright: reportMissingImports=false

from __future__ import annotations

from pathlib import Path

from app.processing.parsers.base import ParsedDocument


class PdfParser:
    def parse(self, file_path: Path) -> ParsedDocument:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for PDF parsing.") from exc

        pages: list[str] = []
        metadata: dict = {}
        with fitz.open(file_path) as document:
            page_count = document.page_count
            metadata = dict(document.metadata or {})
            for page in document:
                pages.append(page.get_text("text"))

        text = "\n\n".join(page.strip() for page in pages if page and page.strip())
        return ParsedDocument(text=text, page_count=page_count, metadata=metadata)
