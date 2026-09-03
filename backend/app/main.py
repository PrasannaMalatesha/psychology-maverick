"""FastAPI application factory.

`create_app` accepts Settings (accept-dependencies-don't-create-them) so tests can
point it at an ephemeral pgvector database. On startup it ensures the pgvector
extension; `/health` reports database reachability.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.db import check_health, ensure_pgvector, make_engine
from app.features.chat.router import router as chat_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_pgvector(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Psychology Maverick — Knowledge Assistant", lifespan=lifespan)
    app.state.engine = engine
    app.state.settings = settings

    @app.get("/health", tags=["health"])
    def health() -> JSONResponse:
        ok = check_health(engine)
        return JSONResponse(
            status_code=200 if ok else 503,
            content={
                "status": "ok" if ok else "degraded",
                "database": "ok" if ok else "unreachable",
            },
        )

    app.include_router(chat_router)
    return app


app = create_app()
