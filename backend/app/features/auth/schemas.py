"""Auth request/response contracts. Email is a plain string (no email-validator dep — a
trust-boundary format check isn't the security control here; the password hash + JWT are)."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisteredUser(BaseModel):
    id: str
    email: str
    role: str
