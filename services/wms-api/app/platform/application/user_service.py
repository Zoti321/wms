"""用户管理：创建、停用、改密、角色分配。"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.platform.domain.permissions import ROLE_ADMIN
from app.platform.infrastructure.models import Role, User
from app.platform.infrastructure.security import hash_password


class UserError(Exception):
    """用户管理业务错误。"""


class UserNotFoundError(UserError):
    """用户不存在。"""


class RoleNotFoundError(UserError):
    """角色不存在。"""


class UserConflictError(UserError):
    """用户名冲突或不可停用。"""


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role_code": user.role.code,
        "status": user.status,
    }


def _get_user(session: Session, user_id: int) -> User:
    user = session.scalars(
        select(User).options(joinedload(User.role)).where(User.id == user_id)
    ).first()
    if user is None:
        raise UserNotFoundError("用户不存在")
    return user


def _get_role_by_code(session: Session, role_code: str) -> Role:
    role = session.scalars(select(Role).where(Role.code == role_code)).first()
    if role is None:
        raise RoleNotFoundError("角色不存在")
    return role


def _count_active_admins(session: Session) -> int:
    return session.scalar(
        select(func.count())
        .select_from(User)
        .join(Role)
        .where(User.status == 1, Role.code == ROLE_ADMIN)
    ) or 0


def create_user(
    session: Session,
    *,
    username: str,
    password: str,
    role_code: str,
) -> dict:
    role = _get_role_by_code(session, role_code)
    user = User(
        username=username,
        password_hash=hash_password(password),
        role_id=role.id,
        status=1,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise UserConflictError("用户名已存在") from exc
    session.refresh(user)
    return _user_to_dict(_get_user(session, user.id))


def deactivate_user(
    session: Session,
    *,
    user_id: int,
    operator_id: int,
) -> dict:
    user = _get_user(session, user_id)
    if user.status != 1:
        raise UserConflictError("用户已停用")
    if user.id == operator_id:
        raise UserConflictError("不能停用当前登录账号")
    if user.role.code == ROLE_ADMIN and _count_active_admins(session) <= 1:
        raise UserConflictError("不能停用最后一个管理员")
    user.status = 0
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def reset_password(session: Session, *, user_id: int, password: str) -> dict:
    user = _get_user(session, user_id)
    if user.status != 1:
        raise UserConflictError("用户已停用")
    user.password_hash = hash_password(password)
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def assign_role(session: Session, *, user_id: int, role_code: str) -> dict:
    user = _get_user(session, user_id)
    role = _get_role_by_code(session, role_code)
    user.role_id = role.id
    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def list_users(session: Session) -> list[dict]:
    rows = session.scalars(
        select(User).options(joinedload(User.role)).order_by(User.id.asc())
    ).all()
    return [_user_to_dict(row) for row in rows]
