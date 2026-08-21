"""盘点锁查询端口：M2 默认未锁；测试可替换。"""

from __future__ import annotations

from collections.abc import Callable

_LockChecker = Callable[[int], bool]

_lock_checker: _LockChecker = lambda _location_id: False


def is_location_locked(location_id: int) -> bool:
    return _lock_checker(location_id)


def set_location_lock_checker(checker: _LockChecker) -> None:
    global _lock_checker
    _lock_checker = checker


def reset_location_lock_checker() -> None:
    global _lock_checker
    _lock_checker = lambda _location_id: False
