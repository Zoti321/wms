"""操作日志写端口与查询。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.platform.infrastructure.models import OperationLog

ACTION_LOGIN = "auth.login"
ACTION_USER_CREATE = "user.create"
ACTION_USER_DEACTIVATE = "user.deactivate"
ACTION_USER_RESET_PASSWORD = "user.reset_password"
ACTION_DICT_CREATE = "dict.create"
ACTION_DICT_UPDATE = "dict.update"
ACTION_DICT_DEACTIVATE = "dict.deactivate"
ACTION_INBOUND_APPROVE = "inbound.approve"
ACTION_OUTBOUND_APPROVE = "outbound.approve"
ACTION_STOCKTAKE_APPROVE = "stocktake.approve"


def record_operation(
    session: Session,
    *,
    operator_id: int,
    operator_name: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    detail: str | None = None,
    commit: bool = False,
) -> None:
    """写入操作日志（不含库存账变细节）。默认由调用方事务提交；commit=True 时立即提交。"""
    session.add(
        OperationLog(
            operator_id=operator_id,
            operator_name=operator_name,
            action=action,
            resource_type=resource_type,
            resource_id=None if resource_id is None else str(resource_id),
            detail=detail,
        )
    )
    session.flush()
    if commit:
        session.commit()


def list_operation_logs(
    session: Session,
    *,
    operator_id: int | None = None,
    action: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[dict]:
    stmt = select(OperationLog)
    if operator_id is not None:
        stmt = stmt.where(OperationLog.operator_id == operator_id)
    if action is not None:
        stmt = stmt.where(OperationLog.action == action)
    if created_from is not None:
        stmt = stmt.where(OperationLog.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(OperationLog.created_at <= created_to)
    stmt = stmt.order_by(OperationLog.id.desc())
    rows = session.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "operator_id": row.operator_id,
            "operator_name": row.operator_name,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "detail": row.detail,
            "created_at": row.created_at.isoformat(sep=" ", timespec="seconds"),
        }
        for row in rows
    ]
