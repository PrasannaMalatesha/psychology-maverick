"""HTTP adapter over the `chat` service — thin by design (ADR-0006).

All routes require an authenticated User (M6); a conversation is owned by its creator, and
reading or resuming someone else's conversation is forbidden (403 — OWASP-API #1 IDOR defense).
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.features.auth.deps import Principal, current_user
from app.features.chat.schemas import Answer, Query

router = APIRouter(tags=["chat"])


class ReviewDecision(BaseModel):
    decision: str  # "approve" serves the held clinical answer; anything else withholds it


def _guard_owner(request: Request, conversation_id: str, user: Principal) -> None:
    owner = request.app.state.chat_service.owner_of(conversation_id)
    if owner is not None and owner != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your conversation")


@router.post("/chat")
def chat(
    payload: Query,
    request: Request,
    response: Response,
    user: Principal = Depends(current_user),
) -> Answer:
    conversation_id = payload.conversation_id or uuid4().hex
    _guard_owner(request, conversation_id, user)  # can't post into another user's conversation
    answer = request.app.state.chat_service.answer(payload.query, conversation_id, user.id)
    response.headers["X-Conversation-Id"] = conversation_id
    return answer


@router.get("/conversations/{conversation_id}")
def conversation(
    conversation_id: str, request: Request, user: Principal = Depends(current_user)
) -> dict:
    _guard_owner(request, conversation_id, user)
    return {
        "conversation_id": conversation_id,
        "turns": request.app.state.chat_service.history(conversation_id),
    }


@router.post("/conversations/{conversation_id}/review")
def review(
    conversation_id: str,
    payload: ReviewDecision,
    request: Request,
    user: Principal = Depends(current_user),
) -> Answer:
    _guard_owner(request, conversation_id, user)
    return request.app.state.chat_service.review(conversation_id, payload.decision)
