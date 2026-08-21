"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.platform.api.deps import CurrentUser, get_current_user
from app.platform.api.schemas import LoginRequest, MeData, TokenData
from app.platform.application.auth_service import InvalidCredentialsError, login_with_password
from app.shared.config import Settings, get_settings
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    body: LoginRequest,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    try:
        result = login_with_password(
            session,
            username=body.username,
            password=body.password,
            settings=settings,
        )
    except InvalidCredentialsError:
        payload, http_status = fail(message="用户名或密码错误")
        return JSONResponse(status_code=http_status, content=payload)

    return JSONResponse(
        content=ok(TokenData(access_token=result.access_token, token_type=result.token_type).model_dump())
    )


@router.get("/me")
def me(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    return ok(
        MeData(
            id=current_user.id,
            username=current_user.username,
            role_code=current_user.role_code,
        ).model_dump()
    )
