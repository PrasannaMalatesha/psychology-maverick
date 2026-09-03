# Backend — Knowledge Assistant

FastAPI modular monolith ([ADR-0005](../docs/adr/0005-modular-monolith-vertical-slices.md)) for the
retrieval-grounded assistant. Module seams follow [ADR-0006](../docs/adr/0006-deep-module-seams.md);
the build is tracked in [docs/ROADMAP.md](../docs/ROADMAP.md), scoped by
[the M1 spec](../docs/specs/M1-rag-chat-slice.md).

## Layout

```
app/
  core/            platform: config, db (Postgres+pgvector), llm/ (the gateway seam)
  features/
    chat/          answer(query) -> Answer  + POST /chat adapter
    corpus/        ingest(source) -> IngestReport   (T2)
    retrieval/     retrieve(query, k) -> ScoredPassage[]   (T2/T3)
tests/             pgvector-backed harness; gateway substituted by FakeGateway
```

## Develop

```bash
cd backend
uv sync                       # install deps into .venv
uv run uvicorn app.main:app --reload   # needs a database (see below)
```

Local database (optional, for running the server):

```bash
docker compose up -d db
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/maverick
```

## Test

Tests spin up their own ephemeral pgvector container — just have Docker running:

```bash
uv run pytest        # full suite
uv run pyright       # type check
uv run ruff check    # lint
uv run lint-imports  # module boundaries (ADR-0005/0006)
```

## Status (T1)

Walking skeleton: `GET /health` (reports DB reachability), the pgvector test harness, and the model
gateway seam with a deterministic fake. `POST /chat` returns 501 until T3. Feature services are shells.
