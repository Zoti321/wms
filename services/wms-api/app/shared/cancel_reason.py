"""取消原因字典校验与 remark 持久化。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.platform.infrastructure.models import DictItem

CANCEL_REASON_DICT_TYPE = "cancel_reason"
CANCEL_REASON_REMARK_PREFIX = "[取消原因: "


class CancelReasonValidationError(Exception):
    """无效的取消原因字典码。"""


def resolve_cancel_reason_name(session: Session, code: str | None) -> str | None:
    if code is None:
        return None
    item = session.scalar(
        select(DictItem).where(
            DictItem.dict_type == CANCEL_REASON_DICT_TYPE,
            DictItem.code == code,
            DictItem.status == 1,
        )
    )
    if item is None:
        raise CancelReasonValidationError("无效的取消原因")
    return item.name


def append_cancel_reason_to_remark(remark: str | None, reason_name: str) -> str:
    prefix = f"{CANCEL_REASON_REMARK_PREFIX}{reason_name}]"
    if remark:
        return f"{prefix} {remark}"
    return prefix
