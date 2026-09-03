"""The Answer contract (M1 spec).

Encodes the grounding decision precisely: a `grounded` Answer carries prose, a
Category, and at least one Citation; an `insufficient_context` Answer carries none
of those. Full validation invariants land in T2/T4; this is the shared shape.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

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


class Query(BaseModel):
    query: str
