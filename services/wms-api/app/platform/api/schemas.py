"""认证相关请求/响应 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeData(BaseModel):
    id: int
    username: str
    role_code: str
