"""The model-gateway interface (ADR-0002, ADR-0006).

Small, provider-agnostic surface. Embedding dimensionality is fixed by the
configured embedding model (default bge-small-en-v1.5 → 384).
"""

from typing import Protocol

EMBEDDING_DIM = 384


class ModelGateway(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed each text into a fixed-dimension vector (EMBEDDING_DIM)."""
        ...

    def synthesize(self, *, context: str, query: str) -> str:
        """Produce answer prose grounded strictly in `context` for `query`."""
        ...
