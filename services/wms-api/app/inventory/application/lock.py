"""库位作业锁端口：is_location_locked / acquire / release；测试可替换查询。"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inventory.infrastructure.lock_models import LocationJobLock

_LockChecker = Callable[[int], bool]
_override_checker: _LockChecker | None = None


class LocationLockError(Exception):
    """作业锁业务错误。"""


class LocationLockConflictError(LocationLockError):
    """库位已被其它作业锁定。"""


def is_location_locked(session: Session, location_id: int) -> bool:
    if _override_checker is not None:
        return _override_checker(location_id)
    row = session.scalars(
        select(LocationJobLock.id).where(LocationJobLock.location_id == location_id)
    ).first()
    return row is not None


def acquire_location_locks(
    session: Session,
    *,
    location_ids: list[int],
    ref_type: str,
    ref_id: int,
) -> None:
    """对库位加作业锁；同一库位同时只能有一把锁。"""
    unique_ids = sorted(set(location_ids))
    if not unique_ids:
        return
    for location_id in unique_ids:
        session.add(
            LocationJobLock(
                location_id=location_id,
                ref_type=ref_type,
                ref_id=ref_id,
            )
        )
    try:
        session.flush()
    except IntegrityError as exc:
        raise LocationLockConflictError("库位已盘点锁定") from exc


def release_location_locks(
    session: Session, *, ref_type: str, ref_id: int
) -> None:
    session.execute(
        delete(LocationJobLock).where(
            LocationJobLock.ref_type == ref_type,
            LocationJobLock.ref_id == ref_id,
        )
    )
    session.flush()


def set_location_lock_checker(checker: _LockChecker) -> None:
    global _override_checker
    _override_checker = checker


def reset_location_lock_checker() -> None:
    global _override_checker
    _override_checker = None
