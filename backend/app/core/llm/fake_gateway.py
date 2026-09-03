"""Deterministic gateway double — the single substituted dependency in tests (ADR-0006).

No network, no cost, fully reproducible: the same input always yields the same
vector and the same synthesized string.
"""

import hashlib
import math

from app.core.llm.gateway import EMBEDDING_DIM


def _deterministic_vector(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    # Expand a digest of the text into `dim` floats, then L2-normalize so the
    # vectors behave like real unit-length embeddings under cosine similarity.
    raw: list[float] = []
    counter = 0
    while len(raw) < dim:
        digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
        raw.extend((b - 127.5) / 127.5 for b in digest)
        counter += 1
    vec = raw[:dim]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeGateway:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_deterministic_vector(t) for t in texts]

    def synthesize(self, *, context: str, query: str) -> str:
        tag = hashlib.sha256(f"{query}|{context}".encode()).hexdigest()[:8]
        return f"[fake answer {tag}] Grounded response to: {query}"
