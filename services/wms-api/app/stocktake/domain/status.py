"""盘点单状态常量。"""

from __future__ import annotations

STATUS_COUNTING = "counting"
STATUS_APPROVED = "approved"
STATUS_CANCELLED = "cancelled"

EDITABLE_STATUSES = frozenset({STATUS_COUNTING})
APPROVE_ALLOWED = frozenset({STATUS_COUNTING})
CANCEL_ALLOWED = frozenset({STATUS_COUNTING})
TERMINAL_STATUSES = frozenset({STATUS_APPROVED, STATUS_CANCELLED})

# 粗粒度角色占位：主管可审核；admin 种子兼容开发环境。
APPROVE_ROLE_CODES = frozenset({"admin", "supervisor"})

LOCK_REF_TYPE = "STOCKTAKE"
