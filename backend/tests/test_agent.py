"""Agent graph: multi-turn via checkpointer, conversation isolation, Postgres persistence."""

import uuid
from pathlib import Path

from sqlalchemy import Engine

from app.core.checkpoint import make_postgres_checkpointer
from app.core.config import Settings
from app.core.llm import FakeGateway
from app.features.assistant.service import AssistantService
from app.features.chat.service import ChatService
from app.features.corpus.service import CorpusService
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def test_multiturn_history_accumulates_and_conversations_isolated(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    chat = ChatService(RetrievalService(engine, FakeGateway()), FakeGateway(), settings)

    chat.answer("what is cognitive behavioral therapy?", "conv-a")
    chat.answer("how is anxiety treated?", "conv-a")
    assert len(chat.history("conv-a")) == 2

    chat.answer("why does sleep matter?", "conv-b")
    assert len(chat.history("conv-b")) == 1
    assert len(chat.history("conv-a")) == 2  # threads isolated


def test_postgres_checkpointer_sets_up_and_persists_across_instances(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    saver = make_postgres_checkpointer(settings.database_url)  # setup() creates checkpoint tables
    cid = "pg-" + uuid.uuid4().hex[:8]

    AssistantService(
        RetrievalService(engine, FakeGateway()), FakeGateway(), settings, saver
    ).answer("what is cognitive behavioral therapy?", cid)
    # A fresh service sharing the same Postgres checkpointer sees the prior turn.
    fresh = AssistantService(
        RetrievalService(engine, FakeGateway()), FakeGateway(), settings, saver
    )
    fresh.answer("how is anxiety treated?", cid)

    assert len(fresh.history(cid)) == 2


def test_chat_returns_conversation_id_header(clean_passages, corpus_service: CorpusService, client):
    corpus_service.ingest(str(FIXTURES))
    r = client.post("/chat", json={"query": "what is cognitive behavioral therapy?"})
    assert r.status_code == 200
    assert r.headers.get("X-Conversation-Id")
