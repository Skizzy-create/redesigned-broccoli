from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class ParsedDocument:
    text: str
    page_count: int
    metadata: dict


class DocumentParser(Protocol):
    def parse(self, file_path: Path) -> ParsedDocument: ...
