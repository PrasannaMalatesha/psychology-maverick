"""HTTP adapter over the `chat` service — thin by design (ADR-0006)."""

from fastapi import APIRouter, Request

from app.features.chat.schemas import Answer, Query

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(payload: Query, request: Request) -> Answer:
    return request.app.state.chat_service.answer(payload.query)
