"""登录用例。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.platform.infrastructure.models import User
from app.platform.infrastructure.security import create_access_token, verify_password
from app.shared.config import Settings


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    user_id: int
    username: str
    token_type: str = "bearer"


class InvalidCredentialsError(Exception):
    """用户名或密码错误（不区分具体原因）。"""


def login_with_password(
    session: Session,
    *,
    username: str,
    password: str,
    settings: Settings,
) -> LoginResult:
    stmt = (
        select(User)
        .options(joinedload(User.role))
        .where(User.username == username, User.status == 1)
    )
    user = session.scalars(stmt).first()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    token = create_access_token(
        subject=str(user.id),
        role_code=user.role.code,
        settings=settings,
        extra={"username": user.username},
    )
    return LoginResult(
        access_token=token,
        user_id=user.id,
        username=user.username,
    )
