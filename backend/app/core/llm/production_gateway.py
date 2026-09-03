"""Real model-gateway adapter (ADR-0002, ADR-0006).

- `embed()` uses local sentence-transformers (default bge-small-en-v1.5, 384-dim) —
  ADR-0002's default local embeddings. Lazy-imported; install the `embeddings` extra
  (`uv sync --extra embeddings`) to use it. Tests use FakeGateway, so CI needs neither.
- `synthesize()` uses LiteLLM (wired in T3).
"""

from typing import Any

from app.core.config import Settings


class ProductionGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model: Any | None = None

    def _embedder(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import (  # type: ignore[import-not-found]
                    SentenceTransformer,
                )
            except ImportError as exc:  # pragma: no cover - exercised only without the extra
                raise RuntimeError(
                    "Local embeddings need the 'embeddings' extra: uv sync --extra embeddings"
                ) from exc
            self._model = SentenceTransformer(self._settings.embedding_model)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._embedder().encode(texts, normalize_embeddings=True)
        return [[float(x) for x in vector] for vector in vectors]

    def synthesize(self, *, context: str, query: str) -> str:
        try:
            import litellm  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError(
                "Synthesis needs the 'synthesis' extra: uv sync --extra synthesis"
            ) from exc
        system = (
            "You are a careful assistant. Answer ONLY from the provided context passages. "
            "If the context does not support an answer, say you don't have enough information. "
            "Do not invent facts."
        )
        response = litellm.completion(
            model=self._settings.synthesis_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
        )
        return response.choices[0].message.content or ""  # type: ignore[union-attr,index]
