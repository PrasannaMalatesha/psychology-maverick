"""AuthService — the write/verify path for accounts and tokens (project.md §9).

Owns registration (argon2), login, refresh-with-rotation, and logout/revocation. Raises small
domain errors; the router maps them to HTTP status. Persistence goes through `core.store`; tokens
and hashing through `auth.security`.
"""

from __future__ import annotations

import uuid

import jwt
from sqlalchemy import Engine

from app.core.config import Settings
from app.core.store import create_user, get_user_by_email, get_user_by_id
from app.features.auth.schemas import RegisteredUser, TokenPair
from app.features.auth.security import (
    RevocationStore,
    decode_token,
    hash_password,
    make_access_token,
    make_refresh_token,
    verify_password,
)


class EmailTakenError(Exception):
    """Registration with an email that already exists."""


class InvalidCredentialsError(Exception):
    """Login with an unknown email or wrong password."""


class InvalidTokenError(Exception):
    """A refresh token that is malformed, expired, the wrong type, or revoked."""


class AuthService:
    def __init__(
        self, engine: Engine, settings: Settings, revocation: RevocationStore
    ) -> None:
        self._engine = engine
        self._settings = settings
        self._revocation = revocation

    def register(self, email: str, password: str, *, role: str = "user") -> RegisteredUser:
        if get_user_by_email(self._engine, email) is not None:
            raise EmailTakenError(email)
        user_id = uuid.uuid4().hex
        create_user(
            self._engine,
            id=user_id,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        return RegisteredUser(id=user_id, email=email, role=role)

    def login(self, email: str, password: str) -> TokenPair:
        user = get_user_by_email(self._engine, email)
        # verify even when the user is missing would be ideal for timing; argon2's cost already
        # dominates, and a constant dummy-verify is deferred with the rest of brute-force hardening.
        if user is None or not verify_password(user.password_hash, password):
            raise InvalidCredentialsError(email)
        return self._issue(user.id, user.role)

    def refresh(self, refresh_token: str) -> TokenPair:
        claims = self._decode_refresh(refresh_token)
        # Rotation: the presented refresh token is single-use — revoke its jti before issuing anew.
        self._revocation.revoke(claims["jti"], self._refresh_ttl_seconds())
        user = get_user_by_id(self._engine, claims["sub"])
        if user is None:
            raise InvalidTokenError("user no longer exists")
        return self._issue(user.id, user.role)

    def logout(self, refresh_token: str) -> None:
        claims = self._decode_refresh(refresh_token)
        self._revocation.revoke(claims["jti"], self._refresh_ttl_seconds())

    # --- internals ---------------------------------------------------------------------------

    def _decode_refresh(self, token: str) -> dict:
        try:
            claims = decode_token(self._settings, token)
        except jwt.InvalidTokenError as exc:  # expired / bad signature / malformed
            raise InvalidTokenError("invalid refresh token") from exc
        if claims.get("type") != "refresh":
            raise InvalidTokenError("not a refresh token")
        if self._revocation.is_revoked(claims.get("jti", "")):
            raise InvalidTokenError("refresh token revoked")
        return claims

    def _issue(self, user_id: str, role: str) -> TokenPair:
        access = make_access_token(self._settings, user_id=user_id, role=role)
        refresh, _jti = make_refresh_token(self._settings, user_id=user_id)
        return TokenPair(access_token=access, refresh_token=refresh)

    def _refresh_ttl_seconds(self) -> int:
        return self._settings.refresh_token_ttl_days * 86_400
