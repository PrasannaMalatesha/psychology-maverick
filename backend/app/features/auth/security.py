"""Auth primitives (project.md §9): argon2 hashing, JWT tokens, refresh revocation.

No provider/framework leakage — pure functions over `Settings` plus a small revocation seam
(in-memory default; Redis adapter for production, lazy-imported behind the `redis` extra).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import Settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except Argon2Error:  # mismatch or malformed hash — both mean "no"
        return False


# --- JWT --------------------------------------------------------------------------------------


def _encode(settings: Settings, payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def make_access_token(settings: Settings, *, user_id: str, role: str) -> str:
    now = datetime.now(UTC)
    return _encode(
        settings,
        {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        },
    )


def make_refresh_token(settings: Settings, *, user_id: str) -> tuple[str, str]:
    """Return (token, jti). The jti identifies this refresh token for rotation/revocation."""
    now = datetime.now(UTC)
    jti = uuid.uuid4().hex
    token = _encode(
        settings,
        {
            "sub": user_id,
            "type": "refresh",
            "jti": jti,
            "exp": now + timedelta(days=settings.refresh_token_ttl_days),
        },
    )
    return token, jti


def decode_token(settings: Settings, token: str) -> dict[str, Any]:
    """Decode + verify signature and expiry. Raises `jwt.InvalidTokenError` on any problem."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# --- refresh-token revocation seam ------------------------------------------------------------


class RevocationStore(Protocol):
    def revoke(self, jti: str, ttl_seconds: int) -> None: ...
    def is_revoked(self, jti: str) -> bool: ...


class InMemoryRevocationStore:
    """Single-process default (tests, local). Production uses Redis so revocation is shared."""

    def __init__(self) -> None:
        self._revoked: dict[str, datetime] = {}  # jti -> expiry

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        self._revoked[jti] = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

    def is_revoked(self, jti: str) -> bool:
        expiry = self._revoked.get(jti)
        if expiry is None:
            return False
        if expiry < datetime.now(UTC):
            del self._revoked[jti]  # expired — let it lapse
            return False
        return True


class RedisRevocationStore:
    """Production revocation over Redis (project.md §9). TTL lets keys expire with the token."""

    def __init__(self, url: str) -> None:
        import redis  # type: ignore[import-not-found]  # pragma: no cover - needs the redis extra

        self._redis = redis.Redis.from_url(url)

    def revoke(self, jti: str, ttl_seconds: int) -> None:  # pragma: no cover - needs live Redis
        self._redis.setex(f"revoked:{jti}", ttl_seconds, "1")

    def is_revoked(self, jti: str) -> bool:  # pragma: no cover - needs live Redis
        return bool(self._redis.exists(f"revoked:{jti}"))


def make_revocation_store(settings: Settings) -> RevocationStore:
    """Redis when configured, else the in-memory default (single process)."""
    if settings.redis_url:
        return RedisRevocationStore(settings.redis_url)
    return InMemoryRevocationStore()
