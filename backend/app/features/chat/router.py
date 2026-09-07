"""HTTP adapter over the `chat` service — thin by design (ADR-0006)."""

from uuid import uuid4

from fastapi import APIRouter, Request, Response

from app.features.chat.schemas import Answer, Query

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(payload: Query, request: Request, response: Response) -> Answer:
    conversation_id = payload.conversation_id or uuid4().hex
    answer = request.app.state.chat_service.answer(payload.query, conversation_id)
    response.headers["X-Conversation-Id"] = conversation_id
    return answer


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: str, request: Request) -> dict:
    return {
        "conversation_id": conversation_id,
        "turns": request.app.state.chat_service.history(conversation_id),
    }
