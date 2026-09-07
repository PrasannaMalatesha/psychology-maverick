"""Cross-feature domain contracts (glossary terms shared across features).

These live in `core` so no feature imports another feature's internals
(ADR-0005/0006). Registers/Categories are corpus/answer vocabulary; the `Answer`
contract is produced by `assistant` and served by `chat`.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Register(StrEnum):
    textbook = "textbook"
    research = "research"
    consumer_health = "consumer_health"


class Category(StrEnum):
    cognitive = "cognitive"
    social = "social"
    clinical = "clinical"
    developmental = "developmental"
    biological = "biological"
    personality = "personality"


class AnswerState(StrEnum):
    grounded = "grounded"
    insufficient_context = "insufficient_context"


class Citation(BaseModel):
    # Wire contract keeps the glossary term "register"; the Python attribute is
    # `source_register` to avoid shadowing a BaseModel member.
    model_config = ConfigDict(populate_by_name=True)

    source_register: Register = Field(alias="register", serialization_alias="register")
    document_title: str
    locator: str
    passage_id: str


class Answer(BaseModel):
    state: AnswerState
    category: Category | None = None
    text: str | None = None
    citations: list[Citation] = []

    @model_validator(mode="after")
    def _enforce_shape(self) -> Self:
        if self.state is AnswerState.grounded:
            if not self.text or self.category is None or not self.citations:
                raise ValueError("grounded Answer requires text, a category, and >=1 citation")
        else:  # insufficient_context
            if self.text is not None or self.category is not None or self.citations:
                raise ValueError(
                    "insufficient_context Answer must carry no text, category, or citations"
                )
        return self


class Query(BaseModel):
    query: str
    conversation_id: str | None = None
