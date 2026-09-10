"""Real model-gateway adapter (ADR-0002, ADR-0006).

Every call routes through the config-driven role registry (`Settings.synthesizer` / `judge` /
`embedder`): each role resolves to an ordered model chain (primary + fallbacks), and `_complete`
tries them in order — first success wins, provider/transport errors fall through to the next.

- `embed()` — the `embedder` role. A `local/<id>` model uses local sentence-transformers
  (default bge-small, 384-dim); any other model id goes through LiteLLM embeddings. Output dim is
  guarded against the store's fixed `EMBEDDING_DIM`.
- `synthesize()` / `is_faithful()` — the `synthesizer` / `judge` roles via LiteLLM chat.

LiteLLM and sentence-transformers are lazy-imported (the `synthesis` / `embeddings` extras); tests
use FakeGateway, so CI needs neither, and this module imports cleanly without them.
"""

from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.core.llm.gateway import EMBEDDING_DIM

_LOCAL_PREFIX = "local/"


def _complete[T](chain: list[str], call: Callable[[str], T]) -> T:
    """Try each model in a role's chain; return the first success, else raise the last error.

    ADR-0002's cross-provider fallback: any provider/transport error moves to the next model.
    """
    last_exc: Exception | None = None
    for model in chain:
        try:
            return call(model)
        except Exception as exc:  # noqa: BLE001 - any provider error is a reason to try the next
            last_exc = exc
    raise RuntimeError(f"all models failed for role chain {chain}") from last_exc


class ProductionGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._st_models: dict[str, Any] = {}  # local sentence-transformers, keyed by model id

    # --- lazy provider imports ---------------------------------------------------------------

    @staticmethod
    def _litellm() -> Any:
        try:
            import litellm  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError(
                "This role needs the 'synthesis' extra: uv sync --extra synthesis"
            ) from exc
        return litellm

    def _sentence_transformer(self, model_id: str) -> Any:
        if model_id not in self._st_models:
            try:
                from sentence_transformers import (  # type: ignore[import-not-found]
                    SentenceTransformer,
                )
            except ImportError as exc:  # pragma: no cover - exercised only without the extra
                raise RuntimeError(
                    "Local embeddings need the 'embeddings' extra: uv sync --extra embeddings"
                ) from exc
            self._st_models[model_id] = SentenceTransformer(model_id)
        return self._st_models[model_id]

    # --- roles -------------------------------------------------------------------------------

    def embed(self, texts: list[str]) -> list[list[float]]:
        def call(model: str) -> list[list[float]]:
            if model.startswith(_LOCAL_PREFIX):
                st = self._sentence_transformer(model.removeprefix(_LOCAL_PREFIX))
                vectors = st.encode(texts, normalize_embeddings=True)
                return [[float(x) for x in v] for v in vectors]
            data = self._litellm().embedding(model=model, input=texts).data
            return [[float(x) for x in row["embedding"]] for row in data]

        vectors = _complete(self._settings.embedder.chain, call)
        # Guard: a remote embedder with a different dimensionality would silently corrupt the
        # store (its vector column is fixed at EMBEDDING_DIM). Fail loudly instead.
        for v in vectors:
            if len(v) != EMBEDDING_DIM:
                raise RuntimeError(
                    f"embedder produced dim {len(v)}, but the store expects {EMBEDDING_DIM}"
                )
        return vectors

    def synthesize(self, *, context: str, query: str) -> str:
        litellm = self._litellm()
        system = (
            "You are a careful assistant. Answer ONLY from the provided context passages. "
            "If the context does not support an answer, say you don't have enough information. "
            "Do not invent facts."
        )

        def call(model: str) -> str:
            response = litellm.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
                ],
            )
            return response.choices[0].message.content or ""

        return _complete(self._settings.synthesizer.chain, call)

    def is_faithful(self, *, context: str, answer: str) -> bool:
        litellm = self._litellm()
        system = (
            "You are a strict faithfulness judge. Decide whether EVERY claim in the ANSWER is "
            "supported by the CONTEXT. Reply with exactly 'yes' or 'no' and nothing else."
        )

        def call(model: str) -> bool:
            response = litellm.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"},
                ],
            )
            verdict = (response.choices[0].message.content or "").strip().lower()
            # Default to unfaithful on an ambiguous verdict — safety errs toward withholding.
            return verdict.startswith("yes")

        return _complete(self._settings.judge.chain, call)
