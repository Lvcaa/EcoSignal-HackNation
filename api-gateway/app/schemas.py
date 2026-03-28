from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ErrorResponse(BaseModel):
    detail: str
