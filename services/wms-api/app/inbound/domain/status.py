"""入库单状态常量。"""

from __future__ import annotations

STATUS_DRAFT = "draft"
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_PUTAWAY = "putaway"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

ORDER_TYPES = frozenset({"purchase", "return", "other"})

EDITABLE_STATUSES = frozenset({STATUS_DRAFT})
PUTAWAY_ALLOWED = frozenset({STATUS_APPROVED, STATUS_PUTAWAY})
TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED})
