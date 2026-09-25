"""Auth dependencies — the public surface other features consume (`chat` imports these).

`current_user` verifies the access token and yields a `Principal`; `require_admin` gates
admin-only routes. Access tokens are short-lived, so they are trusted by signature+expiry alone
(refresh revocation is what logout/rotation guards) — role travels in the token, no DB hit.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.features.auth.security import decode_token

_bearer = HTTPBearer(auto_error=False)
_UNAUTH = {"WWW-Authenticate": "Bearer"}


@dataclass(frozen=True)
class Principal:
    id: str
    role: str


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated", headers=_UNAUTH)
    try:
        claims = decode_token(request.app.state.settings, credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", headers=_UNAUTH
        ) from exc
    if claims.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token", headers=_UNAUTH)
    return Principal(id=claims["sub"], role=claims.get("role", "user"))


def require_admin(user: Principal = Depends(current_user)) -> Principal:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
