"""Structure-aware chunking: split each section into size-capped, overlapping chunks.

Chunks never cross section boundaries, so a chunk's locator is meaningful. IDs are
deterministic (source_ref + locator + index), which is what makes re-ingest idempotent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.features.corpus.documents import Document


@dataclass(frozen=True)
class Chunk:
    passage_id: str
    locator: str
    text: str


def _passage_id(source_ref: str, locator: str, index: int) -> str:
    return hashlib.sha1(f"{source_ref}::{locator}::{index}".encode()).hexdigest()[:24]


def _split(text: str, max_chars: int, overlap: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Prefer a whitespace break near the limit so words aren't split.
        if end < len(text):
            space = text.rfind(" ", start + max_chars - overlap, end)
            if space != -1:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_document(doc: Document, max_chars: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    index = 0
    for locator, section_text in doc.sections:
        for piece in _split(section_text, max_chars, overlap):
            chunks.append(Chunk(_passage_id(doc.source_ref, locator, index), locator, piece))
            index += 1
    return chunks
