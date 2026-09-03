"""The model gateway — the one real seam (ADR-0006).

Two adapters satisfy `ModelGateway`: `LiteLLMGateway` (real) and `FakeGateway`
(deterministic test double). Features depend on the interface, never on a provider SDK.
"""

from app.core.llm.fake_gateway import FakeGateway
from app.core.llm.gateway import ModelGateway

__all__ = ["ModelGateway", "FakeGateway"]
