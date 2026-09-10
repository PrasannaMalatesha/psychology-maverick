"""Application configuration (ADR-0002: config-driven).

Settings are read from the environment / a local `.env`. `get_settings()` is the
single accessor; tests construct `Settings(...)` directly and pass it to
`create_app()` rather than mutating global state.
"""

from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelRole(BaseModel):
    """A logical role (ADR-0002) → its primary model plus an ordered fallback chain.

    Model strings are LiteLLM ids (`provider/model`); the `embedder` uses a `local/<id>`
    primary to mean local sentence-transformers. Swapping/adding a model is a config change,
    never a code change — the whole point of the gateway.
    """

    primary: str
    fallbacks: list[str] = []

    @property
    def chain(self) -> list[str]:
        return [self.primary, *self.fallbacks]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage (ADR-0001: single Postgres + pgvector).
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/maverick"

    # Retrieval / answer policy (consumed from T3 onward; declared here so the
    # thresholds are configuration, never hard-coded — see the M1 spec).
    retrieval_top_k: int = 5
    # 0.5 tuned for bge-small (its similarity floor is high; the live run showed
    # 0.35 admitted off-topic). Final calibration is M7's evals.
    grounding_threshold: float = 0.5

    # Ingestion / chunking (T2).
    chunk_max_chars: int = 1200
    chunk_overlap: int = 150

    # Model gateway roles (ADR-0002): logical role → model, with fallback chains. Defaults per
    # project.md §6 (cheap flash for grading/judging, a premium model for synthesis, local
    # embeddings). Only a Gemini key is available today; fallbacks are as real as the keys present.
    synthesizer: ModelRole = ModelRole(primary="gemini/gemini-1.5-pro")
    judge: ModelRole = ModelRole(primary="gemini/gemini-1.5-flash")
    embedder: ModelRole = ModelRole(primary="local/BAAI/bge-small-en-v1.5")

    # Safety (ADR-0004). Crisis resources and the disclaimer are text so they are tuned /
    # region-overridden without code changes. A grounded *clinical* answer whose top passage
    # scores below the confidence threshold is held for human review; tests set it to 0.0 to
    # opt out (as with grounding_threshold), and to 1.0 to force review deterministically.
    clinical_confidence_threshold: float = 0.8
    crisis_resources: str = (
        "It sounds like you may be going through something painful, and you deserve support "
        "right now. If you are thinking about harming yourself or ending your life, please reach "
        "out: in the US, call or text 988 (Suicide & Crisis Lifeline). Anywhere, you can find a "
        "helpline at https://findahelpline.com. If you are in immediate danger, call your local "
        "emergency number. You are not alone, and help is available."
    )
    clinical_disclaimer: str = (
        "This is general information drawn from published sources, not medical advice, a "
        "diagnosis, or a treatment plan. For guidance about your own situation, please consult "
        "a licensed clinician."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
