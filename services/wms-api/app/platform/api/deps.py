"""FastAPI 依赖：数据库会话、当前操作者与角色鉴权。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.platform.domain.permissions import has_permission
from app.platform.infrastructure.models import User
from app.platform.infrastructure.security import decode_access_token
from app.shared.config import Settings, get_settings
from app.shared.db import get_db
from app.shared.response import fail

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str
    role_code: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        body, _ = fail(message="未登录或 Token 无效")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=body)

    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        body, _ = fail(message="未登录或 Token 无效")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=body) from None

    stmt = (
        select(User)
        .options(joinedload(User.role))
        .where(User.id == user_id, User.status == 1)
    )
    user = session.scalars(stmt).first()
    if user is None:
        body, _ = fail(message="未登录或 Token 无效")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=body)

    return CurrentUser(id=user.id, username=user.username, role_code=user.role.code)


def require_permissions(*perms: str) -> Callable[..., CurrentUser]:
    """接口级角色鉴权：缺权限返回 403（与未登录 401 区分）。"""

    def _dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not has_permission(current_user.role_code, *perms):
            body, _ = fail(code=40300, message="无权限执行该操作", http_status=403)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=body)
        return current_user

    return _dependency
