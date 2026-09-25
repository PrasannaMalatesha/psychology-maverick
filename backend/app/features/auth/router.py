"""HTTP adapter over `AuthService` — thin; maps domain errors to status codes (ADR-0006)."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.features.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisteredUser,
    RegisterRequest,
    TokenPair,
)
from app.features.auth.service import (
    AuthService,
    EmailTakenError,
    InvalidCredentialsError,
    InvalidTokenError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(request: Request) -> AuthService:
    return request.app.state.auth_service


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request) -> RegisteredUser:
    try:
        return _service(request).register(payload.email, payload.password)
    except EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None


@router.post("/login")
def login(payload: LoginRequest, request: Request) -> TokenPair:
    try:
        return _service(request).login(payload.email, payload.password)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from None


@router.post("/refresh")
def refresh(payload: RefreshRequest, request: Request) -> TokenPair:
    try:
        return _service(request).refresh(payload.refresh_token)
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, request: Request) -> Response:
    try:
        _service(request).logout(payload.refresh_token)
    except InvalidTokenError:
        pass  # logging out an already-invalid token is a no-op, not an error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
