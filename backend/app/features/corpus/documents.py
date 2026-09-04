"""Load source documents into a common shape for chunking.

Supports markdown/text (with optional `--- key: value ---` front matter and
heading-based sections) and PDF (pypdf, one section per page). Register is taken
from front matter, else inferred from the parent directory name
(textbooks→textbook, articles→research, mental_health→consumer_health).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.contracts import Category, Register

_DIR_REGISTER = {
    "textbooks": Register.textbook,
    "articles": Register.research,
    "mental_health": Register.consumer_health,
}


@dataclass(frozen=True)
class Document:
    title: str
    register: Register
    category: Category | None
    source_ref: str
    sections: list[tuple[str, str]]  # (locator, text)


def _infer_register(path: Path, override: str | None) -> Register:
    if override:
        return Register(override)
    for part in path.parts:
        if part in _DIR_REGISTER:
            return _DIR_REGISTER[part]
    raise ValueError(f"Cannot determine register for {path}: no front matter, no known parent dir")


def _parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    block = raw[3:end].strip()
    body = raw[end + 4 :].lstrip("\n")
    meta = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def _split_sections(body: str, fallback_locator: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    locator = fallback_locator
    buf: list[str] = []
    for line in body.splitlines():
        if line.lstrip().startswith("#"):
            if buf and "".join(buf).strip():
                sections.append((locator, "\n".join(buf).strip()))
            locator = line.lstrip("#").strip() or fallback_locator
            buf = []
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        sections.append((locator, "\n".join(buf).strip()))
    return sections or [(fallback_locator, body.strip())]


def _load_markdown(path: Path) -> Document:
    meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
    title = meta.get("title", path.stem)
    category = Category(meta["category"]) if meta.get("category") else None
    return Document(
        title=title,
        register=_infer_register(path, meta.get("register")),
        category=category,
        source_ref=str(path),
        sections=_split_sections(body, fallback_locator=title),
    )


def _load_pdf(path: Path) -> Document:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    sections = [
        (f"p.{i + 1}", (page.extract_text() or "").strip())
        for i, page in enumerate(reader.pages)
    ]
    sections = [(loc, txt) for loc, txt in sections if txt]
    return Document(
        title=path.stem,
        register=_infer_register(path, None),
        category=None,
        source_ref=str(path),
        sections=sections,
    )


def load_documents(root: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            docs.append(_load_markdown(path))
        elif path.suffix.lower() == ".pdf":
            docs.append(_load_pdf(path))
    return docs
