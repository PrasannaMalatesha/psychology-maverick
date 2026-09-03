"""The deterministic gateway double — the one substituted seam (ADR-0006).

Determinism is the property later tickets depend on; assert it here.
"""

from app.core.llm import FakeGateway
from app.core.llm.gateway import EMBEDDING_DIM


def test_embed_is_fixed_dim_and_deterministic():
    gw = FakeGateway()
    first = gw.embed(["hello", "world"])
    assert len(first) == 2
    assert all(len(v) == EMBEDDING_DIM for v in first)
    # Same input -> same vector.
    assert gw.embed(["hello"])[0] == first[0]
    # Different input -> different vector.
    assert first[0] != first[1]


def test_synthesize_is_deterministic_and_references_query():
    gw = FakeGateway()
    q = "What is cognitive behavioral therapy?"
    out = gw.synthesize(context="CBT is a structured therapy.", query=q)
    assert out == gw.synthesize(context="CBT is a structured therapy.", query=q)
    assert q in out
