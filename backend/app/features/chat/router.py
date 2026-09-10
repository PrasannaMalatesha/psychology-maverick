"""HTTP adapter over the `chat` service — thin by design (ADR-0006)."""

from uuid import uuid4

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.features.chat.schemas import Answer, Query

router = APIRouter(tags=["chat"])


class ReviewDecision(BaseModel):
    decision: str  # "approve" serves the held clinical answer; anything else withholds it


@router.post("/chat")
def chat(payload: Query, request: Request, response: Response) -> Answer:
    conversation_id = payload.conversation_id or uuid4().hex
    answer = request.app.state.chat_service.answer(payload.query, conversation_id)
    response.headers["X-Conversation-Id"] = conversation_id
    return answer


@router.post("/conversations/{conversation_id}/review")
def review(conversation_id: str, payload: ReviewDecision, request: Request) -> Answer:
    return request.app.state.chat_service.review(conversation_id, payload.decision)


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: str, request: Request) -> dict:
    return {
        "conversation_id": conversation_id,
        "turns": request.app.state.chat_service.history(conversation_id),
    }
