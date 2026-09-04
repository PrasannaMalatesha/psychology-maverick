"""Deterministic gateway double — the single substituted dependency in tests (ADR-0006).

Embeddings are token-overlap bags: texts that share words get positive cosine
similarity, unrelated texts get ~0. That's the minimum fidelity needed to test
retrieval ordering and the grounding threshold without a real model.
"""

import hashlib
import math
import re

from app.core.llm.gateway import EMBEDDING_DIM

_TOKEN = re.compile(r"[a-z0-9]+")


def _bag_vector(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    for token in _TOKEN.findall(text.lower()):
        idx = int(hashlib.sha256(token.encode()).hexdigest(), 16) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeGateway:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_bag_vector(t) for t in texts]

    def synthesize(self, *, context: str, query: str) -> str:
        tag = hashlib.sha256(f"{query}|{context}".encode()).hexdigest()[:8]
        return f"[fake answer {tag}] Grounded response to: {query}"
