"""Load source documents into a common shape for chunking.

Formats: markdown/text (optional `--- key: value ---` front matter, heading-based
sections) and PDF (pypdf, one section per page). Register is taken from front
matter, else inferred from the parent directory (textbooks→textbook,
articles→research, mental_health→consumer_health). Every document gets a Category
(front matter → per-register default).

PLOS ships article metadata as Solr-shaped JSON (id + title only, no body), so JSON
is read as a *title manifest* — it renames the matching article PDFs — not as a
passage source (the article text is the PDFs).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.core.contracts import Category, Register

_DIR_REGISTER = {
    "textbooks": Register.textbook,
    "articles": Register.research,
    "mental_health": Register.consumer_health,
}

# Coarse per-register default when a source carries no explicit Category. Overridden
# by front matter where present; a real per-passage classifier is future work (M7).
_DEFAULT_CATEGORY = {
    Register.textbook: Category.cognitive,
    Register.research: Category.clinical,
    Register.consumer_health: Category.clinical,
}


@dataclass(frozen=True)
class Document:
    title: str
    register: Register
    category: Category
    source_ref: str
    sections: list[tuple[str, str]]  # (locator, text)


def _infer_register(path: Path, override: str | None) -> Register:
    if override:
        return Register(override)
    for part in path.parts:
        if part in _DIR_REGISTER:
            return _DIR_REGISTER[part]
    raise ValueError(f"Cannot determine register for {path}: no front matter, no known parent dir")


def _category(override: str | None, register: Register) -> Category:
    return Category(override) if override else _DEFAULT_CATEGORY[register]


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


def _load_title_manifest(root: Path) -> dict[str, str]:
    """Map an article's trailing DOI segment (e.g. '0197002') to its title, from PLOS JSON."""
    manifest: dict[str, str] = {}
    for path in root.rglob("*.json"):
        try:
            docs = json.loads(path.read_text(encoding="utf-8")).get("response", {}).get("docs", [])
        except (ValueError, OSError):
            continue
        for doc in docs:
            doc_id, title = doc.get("id"), doc.get("title_display")
            if doc_id and title:
                manifest[doc_id.rsplit(".", 1)[-1]] = title
    return manifest


def _manifest_title(stem: str, manifest: dict[str, str]) -> str | None:
    for key, title in manifest.items():
        if key in stem:
            return title
    return None


def _load_markdown(path: Path, manifest: dict[str, str]) -> Document:
    meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
    register = _infer_register(path, meta.get("register"))
    title = meta.get("title") or _manifest_title(path.stem, manifest) or path.stem
    return Document(
        title=title,
        register=register,
        category=_category(meta.get("category"), register),
        source_ref=str(path),
        sections=_split_sections(body, fallback_locator=title),
    )


def _load_pdf(path: Path, manifest: dict[str, str]) -> Document:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    sections = [
        (f"p.{i + 1}", (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages)
    ]
    sections = [(loc, txt) for loc, txt in sections if txt]
    register = _infer_register(path, None)
    return Document(
        title=_manifest_title(path.stem, manifest) or path.stem,
        register=register,
        category=_category(None, register),
        source_ref=str(path),
        sections=sections,
    )


def load_documents(root: Path) -> tuple[list[Document], int]:
    """Load all supported documents under root. Returns (documents, skipped_count).

    A source that fails to parse or yields no text is skipped with a warning so one
    bad file never aborts a whole-corpus run.
    """
    manifest = _load_title_manifest(root)
    docs: list[Document] = []
    skipped = 0
    for path in sorted(root.rglob("*")):
        suffix = path.suffix.lower()
        if suffix not in {".md", ".txt", ".pdf"}:
            continue
        try:
            doc = (
                _load_markdown(path, manifest)
                if suffix in {".md", ".txt"}
                else _load_pdf(path, manifest)
            )
        except Exception as exc:  # noqa: BLE001 - skip any unreadable source, keep going
            print(f"skip {path}: {exc}")
            skipped += 1
            continue
        if not any(text.strip() for _, text in doc.sections):
            print(f"skip {path}: no extractable text")
            skipped += 1
            continue
        docs.append(doc)
    return docs, skipped
