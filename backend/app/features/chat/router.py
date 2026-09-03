"""HTTP adapter over the `chat` service — thin by design (ADR-0006).

The seam exists now so the shape is fixed; the handler returns 501 until the
`chat.answer` grounded path lands in T3.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.features.chat.schemas import Query

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(_: Query) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "POST /chat is implemented in T3 (#3)"},
    )
