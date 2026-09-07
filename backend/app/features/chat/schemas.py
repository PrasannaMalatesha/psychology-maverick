"""Answer contract for the chat feature — re-exported from core.contracts.

The contract lives in `core` so `assistant` (which builds Answers) and `chat`
(which serves them) both depend on it without crossing feature boundaries.
"""

from app.core.contracts import Answer, AnswerState, Category, Citation, Query, Register

__all__ = ["Answer", "AnswerState", "Category", "Citation", "Query", "Register"]
