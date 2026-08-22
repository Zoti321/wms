"""出库单状态常量。"""

from __future__ import annotations

STATUS_DRAFT = "draft"
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_PICKING = "picking"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

ORDER_TYPES = frozenset({"sales", "material", "other"})

EDITABLE_STATUSES = frozenset({STATUS_DRAFT})
APPROVE_ALLOWED = frozenset({STATUS_PENDING})
PICK_ALLOWED = frozenset({STATUS_APPROVED, STATUS_PICKING})
CANCEL_RELEASE_STATUSES = frozenset({STATUS_APPROVED, STATUS_PICKING})
TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED})
