from __future__ import annotations

from pathlib import Path

from app.core.exceptions import UnsupportedMediaTypeError
from app.processing.parsers.base import DocumentParser
from app.processing.parsers.docx_parser import DocxParser
from app.processing.parsers.pdf_parser import PdfParser


class DocumentParserFactory:
    _allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    @classmethod
    def allowed_content_types(cls) -> set[str]:
        return set(cls._allowed_types)

    @classmethod
    def from_file(cls, content_type: str | None, filename: str) -> DocumentParser:
        normalized_type = (content_type or "").lower().strip()
        suffix = Path(filename).suffix.lower()

        if normalized_type == "application/pdf" or suffix == ".pdf":
            return PdfParser()

        if normalized_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or suffix == ".docx":
            return DocxParser()

        allowed = ", ".join(sorted(cls._allowed_types))
        raise UnsupportedMediaTypeError(
            message=f"Unsupported file type. Allowed content-types: {allowed}",
            code="unsupported_media_type",
        )
