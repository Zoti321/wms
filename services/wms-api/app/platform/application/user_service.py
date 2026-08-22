"""用户角色分配（管理员）。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.platform.infrastructure.models import Role, User


class UserError(Exception):
    """用户管理业务错误。"""


class UserNotFoundError(UserError):
    """用户不存在。"""


class RoleNotFoundError(UserError):
    """角色不存在。"""


def assign_role(session: Session, *, user_id: int, role_code: str) -> dict:
    user = session.scalars(
        select(User).options(joinedload(User.role)).where(User.id == user_id)
    ).first()
    if user is None:
        raise UserNotFoundError("用户不存在")
    role = session.scalars(select(Role).where(Role.code == role_code)).first()
    if role is None:
        raise RoleNotFoundError("角色不存在")
    user.role_id = role.id
    session.commit()
    session.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "role_code": role.code,
        "status": user.status,
    }


def list_users(session: Session) -> list[dict]:
    rows = session.scalars(
        select(User).options(joinedload(User.role)).order_by(User.id.asc())
    ).all()
    return [
        {
            "id": row.id,
            "username": row.username,
            "role_code": row.role.code,
            "status": row.status,
        }
        for row in rows
    ]
