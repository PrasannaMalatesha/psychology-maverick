"""Postgres checkpointer for the agent graph — multi-turn persistence (ADR-0001/0005).

Tests use an in-memory saver; this is the durable one for real runs. `setup()` is
idempotent and creates the checkpoint tables in the same database as the passages.
"""

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row


def make_postgres_checkpointer(database_url: str) -> PostgresSaver:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    # ponytail: single connection; use a psycopg pool if checkpoint throughput matters.
    conn = psycopg.connect(conninfo, autocommit=True, row_factory=dict_row)  # type: ignore[arg-type]
    saver = PostgresSaver(conn)  # type: ignore[arg-type]
    saver.setup()
    return saver
