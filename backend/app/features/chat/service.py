"""The `chat` service — the deep answer engine (ADR-0006).

Interface is one method, `answer(query) -> Answer`. It accepts its dependencies
(retrieval + the model gateway + settings) rather than constructing them. T3 implements
the grounded path; T4 adds the Insufficient-Context threshold + citation-integrity
guardrails, and T5 wraps this in a trace — none of which change this interface.
"""

from app.core.config import Settings
from app.core.llm.gateway import ModelGateway
from app.features.chat.schemas import Answer, AnswerState, Citation
from app.features.retrieval.service import RetrievalService


class ChatService:
    def __init__(
        self, retrieval: RetrievalService, gateway: ModelGateway, settings: Settings
    ) -> None:
        self._retrieval = retrieval
        self._gateway = gateway
        self._settings = settings

    def answer(self, query: str) -> Answer:
        passages = self._retrieval.retrieve(query, self._settings.retrieval_top_k)
        grounded = [p for p in passages if p.score >= self._settings.grounding_threshold]
        if not grounded:
            # Grounded-or-silent (ADR-0004): nothing clears the threshold, so we
            # decline rather than synthesize from weak or absent evidence.
            return Answer(state=AnswerState.insufficient_context)

        context = "\n\n".join(f"[{i + 1}] {p.text}" for i, p in enumerate(grounded))
        prose = self._gateway.synthesize(context=context, query=query)
        # Citations are built from the retrieved passages, so no citation can
        # reference anything outside the retrieved set (no-fabrication by construction).
        citations = [
            Citation(
                register=p.register,
                document_title=p.document_title,
                locator=p.locator,
                passage_id=p.passage_id,
            )
            for p in grounded
        ]
        return Answer(
            state=AnswerState.grounded,
            category=grounded[0].category,
            text=prose,
            citations=citations,
        )
