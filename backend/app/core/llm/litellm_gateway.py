"""Real model-gateway adapter over LiteLLM (ADR-0002).

Shell for T1: the interface and role wiring exist; the actual LiteLLM calls are
implemented in T3 (synthesis) / T2 (embeddings), where `litellm` becomes a
dependency. `litellm` is imported lazily so the package is not required until a
real call is made.
"""

from app.core.config import Settings


class LiteLLMGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("LiteLLM embeddings are wired in T2")

    def synthesize(self, *, context: str, query: str) -> str:
        raise NotImplementedError("LiteLLM synthesis is wired in T3")
