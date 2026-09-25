"""FastAPI application factory.

`create_app` accepts Settings (accept-dependencies-don't-create-them) so tests can
point it at an ephemeral pgvector database. On startup it ensures the pgvector
extension; `/health` reports database reachability.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.db import check_health, ensure_pgvector, make_engine
from app.core.llm.gateway import ModelGateway
from app.core.llm.production_gateway import ProductionGateway
from app.core.observability import LangfuseTracer, Tracer
from app.core.store import corpus_stats, init_store
from app.features.auth.deps import Principal, require_admin
from app.features.auth.router import router as auth_router
from app.features.auth.security import make_revocation_store
from app.features.auth.service import AuthService
from app.features.chat.router import router as chat_router
from app.features.chat.service import ChatService
from app.features.retrieval.service import RetrievalService

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def create_app(
    settings: Settings | None = None,
    gateway: ModelGateway | None = None,
    tracer: Tracer | None = None,
    checkpointer: object | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    gateway = gateway or ProductionGateway(settings)
    tracer = tracer or LangfuseTracer(settings)
    # checkpointer=None -> ChatService uses an in-memory saver; deploy passes a
    # Postgres checkpointer (app.core.checkpoint.make_postgres_checkpointer).
    chat_service = ChatService(
        RetrievalService(engine, gateway), gateway, settings, tracer, checkpointer, engine=engine
    )
    auth_service = AuthService(engine, settings, make_revocation_store(settings))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_pgvector(engine)
        init_store(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Psychology Maverick — Knowledge Assistant", lifespan=lifespan)
    app.state.engine = engine
    app.state.settings = settings
    app.state.chat_service = chat_service
    app.state.auth_service = auth_service

    # CORS allow-list (Vercel origin at deploy) + baseline security headers (project.md §9).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(_SECURITY_HEADERS)
        return response

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

    @app.get("/admin/corpus-stats", tags=["admin"])
    def admin_corpus_stats(_: Principal = Depends(require_admin)) -> list[dict]:
        # RBAC: admin manages the corpus (CONTEXT.md). require_admin → 403 for non-admins.
        return [
            {"register": s.register, "documents": s.documents, "passages": s.passages}
            for s in corpus_stats(engine)
        ]

    app.include_router(auth_router)
    app.include_router(chat_router)
    return app


app = create_app()
