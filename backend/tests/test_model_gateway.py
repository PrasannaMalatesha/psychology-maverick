"""M5 model gateway (ADR-0002): role chains, cross-provider fallback, embedder dim guard.

Pure/offline — the routing and fallback control flow is what carries risk, and it is exercised
without any live provider call. Real LiteLLM/sentence-transformers calls stay a live-run concern.
"""

import pytest

from app.core.config import ModelRole, Settings
from app.core.llm.gateway import EMBEDDING_DIM
from app.core.llm.production_gateway import ProductionGateway, _complete


def test_role_chain_is_primary_then_fallbacks():
    role = ModelRole(primary="a", fallbacks=["b", "c"])
    assert role.chain == ["a", "b", "c"]
    assert ModelRole(primary="only").chain == ["only"]


def test_complete_returns_primary_without_trying_fallbacks():
    tried: list[str] = []

    def call(model: str) -> str:
        tried.append(model)
        return f"ok:{model}"

    assert _complete(["primary", "backup"], call) == "ok:primary"
    assert tried == ["primary"]  # backup never touched


def test_complete_falls_through_to_first_working_model():
    tried: list[str] = []

    def call(model: str) -> str:
        tried.append(model)
        if model != "third":
            raise RuntimeError(f"{model} down")
        return "served"

    assert _complete(["first", "second", "third"], call) == "served"
    assert tried == ["first", "second", "third"]


def test_complete_raises_when_all_models_fail():
    def call(model: str) -> str:
        raise RuntimeError(f"{model} down")

    with pytest.raises(RuntimeError, match="all models failed"):
        _complete(["a", "b"], call)


# --- embedder dim guard (offline via a stubbed local model) --------------------------------

class _FakeST:
    def __init__(self, dim: int) -> None:
        self._dim = dim

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> list[list[float]]:
        return [[0.1] * self._dim for _ in texts]


def _gateway_with_local_embedder(dim: int) -> ProductionGateway:
    gw = ProductionGateway(Settings(embedder=ModelRole(primary="local/fake")))
    gw._st_models["fake"] = _FakeST(dim)  # pre-seed the cache so no real model loads
    return gw


def test_embed_returns_vectors_at_expected_dim():
    vectors = _gateway_with_local_embedder(EMBEDDING_DIM).embed(["hello", "world"])
    assert len(vectors) == 2
    assert all(len(v) == EMBEDDING_DIM for v in vectors)


def test_embed_rejects_wrong_dimensionality():
    with pytest.raises(RuntimeError, match="expects"):
        _gateway_with_local_embedder(EMBEDDING_DIM + 1).embed(["hello"])
