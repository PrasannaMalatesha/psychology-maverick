"""The `chat` service — the deep answer engine (ADR-0006).

Interface is one method, `answer(query) -> Answer`. It accepts its dependencies
(retrieval, the model gateway, settings, a tracer) rather than constructing them.
The grounded-vs-Insufficient-Context policy and citation assembly live behind this
interface; each call emits one trace with a `retrieve` span and, when grounded, a
`synthesize` span.
"""

from app.core.config import Settings
from app.core.llm.gateway import ModelGateway
from app.core.observability import NullTracer, Tracer
from app.features.chat.schemas import Answer, AnswerState, Citation
from app.features.retrieval.service import RetrievalService


class ChatService:
    def __init__(
        self,
        retrieval: RetrievalService,
        gateway: ModelGateway,
        settings: Settings,
        tracer: Tracer | None = None,
    ) -> None:
        self._retrieval = retrieval
        self._gateway = gateway
        self._settings = settings
        self._tracer = tracer or NullTracer()

    def answer(self, query: str) -> Answer:
        with self._tracer.trace("chat.answer", query=query) as trace:
            with trace.span("retrieve"):
                passages = self._retrieval.retrieve(query, self._settings.retrieval_top_k)

            grounded = [p for p in passages if p.score >= self._settings.grounding_threshold]
            if not grounded:
                # Grounded-or-silent (ADR-0004): nothing clears the threshold, so we
                # decline rather than synthesize from weak or absent evidence.
                return Answer(state=AnswerState.insufficient_context)

            context = "\n\n".join(f"[{i + 1}] {p.text}" for i, p in enumerate(grounded))
            with trace.span("synthesize"):
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
