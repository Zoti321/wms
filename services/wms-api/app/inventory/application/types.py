"""库存记账共享类型与常量（对外 re-export 经 inventory_service）。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ALERT_STATUS_OPEN = "open"
ALERT_STATUS_CLEARED = "cleared"

INCREASE_SCOPE = "inventory.increase"
ALLOCATE_SCOPE = "inventory.allocate"
DEDUCT_SCOPE = "inventory.deduct"
RELEASE_SCOPE = "inventory.release"
ADJUST_SCOPE = "inventory.adjust"

REF_TYPE_PUTAWAY = "PUTAWAY"
REF_TYPE_ALLOCATE = "ALLOCATE"
REF_TYPE_PICK = "PICK"
REF_TYPE_RELEASE = "RELEASE"
REF_TYPE_STOCKTAKE = "STOCKTAKE"


class InventoryError(Exception):
    """库存记账业务错误。"""


class InventoryConflictError(InventoryError):
    """乐观锁冲突或幂等冲突。"""


class InventoryInsufficientError(InventoryError):
    """可用/冻结不足以完成记账。"""


@dataclass(frozen=True)
class MutationResult:
    inventory_id: int
    qty_on_hand: str
    qty_frozen: str
    qty_available: str
    version: int
    ledger_id: int
    replayed: bool = False


# 兼容既有调用方命名
IncreaseResult = MutationResult


def fmt_qty(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def available_qty(on_hand: Decimal, frozen: Decimal) -> Decimal:
    return on_hand - frozen
