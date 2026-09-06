"""The Answer contract (M1 spec).

Encodes the grounding decision precisely: a `grounded` Answer carries prose, a
Category, and at least one Citation; an `insufficient_context` Answer carries none
of those. Full validation invariants land in T2/T4; this is the shared shape.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.contracts import Category, Register

__all__ = ["Register", "Category", "AnswerState", "Citation", "Answer", "Query"]


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
