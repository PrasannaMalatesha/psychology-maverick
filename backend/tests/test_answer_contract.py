"""The Answer contract enforces its own shape (M2·T2)."""

import pytest
from pydantic import ValidationError

from app.core.contracts import Category, Register
from app.features.chat.schemas import Answer, AnswerState, Citation


def _cite() -> Citation:
    return Citation(register=Register.textbook, document_title="Doc", locator="p.1", passage_id="x")


def test_valid_grounded_and_insufficient_construct():
    Answer(state=AnswerState.grounded, category=Category.clinical, text="hi", citations=[_cite()])
    Answer(state=AnswerState.insufficient_context)  # defaults: no text/category/citations


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "state": AnswerState.grounded,
            "category": Category.clinical,
            "text": "hi",
            "citations": [],
        },
        {"state": AnswerState.grounded, "category": None, "text": "hi", "citations": [_cite()]},
        {
            "state": AnswerState.grounded,
            "category": Category.clinical,
            "text": None,
            "citations": [_cite()],
        },
        {
            "state": AnswerState.grounded,
            "category": Category.clinical,
            "text": "",
            "citations": [_cite()],
        },
    ],
)
def test_ill_formed_grounded_raises(kwargs):
    with pytest.raises(ValidationError):
        Answer(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"state": AnswerState.insufficient_context, "text": "x"},
        {"state": AnswerState.insufficient_context, "category": Category.clinical},
        {"state": AnswerState.insufficient_context, "citations": [_cite()]},
    ],
)
def test_ill_formed_insufficient_raises(kwargs):
    with pytest.raises(ValidationError):
        Answer(**kwargs)
