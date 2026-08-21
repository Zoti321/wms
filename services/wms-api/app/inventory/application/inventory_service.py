"""库存记账端口：本里程碑提供 increase；余额维度仓库+SKU+库位。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.inventory.infrastructure.models import (
    IdempotencyRecord,
    InventoryBalance,
    InventoryLedger,
)

INCREASE_SCOPE = "inventory.increase"
REF_TYPE_PUTAWAY = "PUTAWAY"


class InventoryError(Exception):
    """库存记账业务错误。"""


class InventoryConflictError(InventoryError):
    """乐观锁冲突或幂等冲突。"""


@dataclass(frozen=True)
class IncreaseResult:
    inventory_id: int
    qty_on_hand: str
    qty_frozen: str
    qty_available: str
    version: int
    ledger_id: int
    replayed: bool = False


def _fmt(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def _available(on_hand: Decimal, frozen: Decimal) -> Decimal:
    return on_hand - frozen


def _load_idempotent(
    session: Session, *, scope: str, key: str
) -> IncreaseResult | None:
    row = session.scalars(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == key,
        )
    ).first()
    if row is None:
        return None
    payload = json.loads(row.response_json)
    return IncreaseResult(**payload)


def _store_idempotent(
    session: Session, *, scope: str, key: str, result: IncreaseResult
) -> None:
    session.add(
        IdempotencyRecord(
            scope=scope,
            idempotency_key=key,
            response_json=json.dumps(asdict(result)),
        )
    )


def load_increase_idempotent(
    session: Session, *, idempotency_key: str
) -> IncreaseResult | None:
    existing = _load_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key
    )
    if existing is None:
        return None
    return IncreaseResult(
        inventory_id=existing.inventory_id,
        qty_on_hand=existing.qty_on_hand,
        qty_frozen=existing.qty_frozen,
        qty_available=existing.qty_available,
        version=existing.version,
        ledger_id=existing.ledger_id,
        replayed=True,
    )


def increase(
    session: Session,
    *,
    warehouse_id: int,
    sku_id: int,
    location_id: int,
    qty: Decimal,
    ref_type: str,
    ref_id: int,
    ref_line_id: int | None,
    ref_no: str,
    operator_id: int,
    idempotency_key: str,
) -> IncreaseResult:
    """增加在库数量并写流水。同一幂等键重复调用返回首次结果。"""
    if qty <= 0:
        raise InventoryError("上架数量必须大于 0")

    existing = _load_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key
    )
    if existing is not None:
        return IncreaseResult(
            inventory_id=existing.inventory_id,
            qty_on_hand=existing.qty_on_hand,
            qty_frozen=existing.qty_frozen,
            qty_available=existing.qty_available,
            version=existing.version,
            ledger_id=existing.ledger_id,
            replayed=True,
        )

    balance = session.scalars(
        select(InventoryBalance).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.sku_id == sku_id,
            InventoryBalance.location_id == location_id,
        )
    ).first()

    if balance is None:
        balance = InventoryBalance(
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            qty_on_hand=Decimal("0"),
            qty_frozen=Decimal("0"),
            version=0,
        )
        session.add(balance)
        session.flush()

    expected_version = balance.version
    new_on_hand = balance.qty_on_hand + qty
    new_version = expected_version + 1

    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance.id,
            InventoryBalance.version == expected_version,
        )
        .values(qty_on_hand=new_on_hand, version=new_version)
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")

    session.refresh(balance)
    ledger = InventoryLedger(
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        change_qty=qty,
        bal_qty=balance.qty_on_hand,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    session.add(ledger)
    session.flush()

    increase_result = IncreaseResult(
        inventory_id=balance.id,
        qty_on_hand=_fmt(balance.qty_on_hand),
        qty_frozen=_fmt(balance.qty_frozen),
        qty_available=_fmt(_available(balance.qty_on_hand, balance.qty_frozen)),
        version=balance.version,
        ledger_id=ledger.id,
        replayed=False,
    )
    _store_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key, result=increase_result
    )
    session.flush()
    return increase_result


def list_balances(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    location_id: int | None = None,
) -> list[dict]:
    stmt = select(InventoryBalance)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryBalance.warehouse_id == warehouse_id)
    if sku_id is not None:
        stmt = stmt.where(InventoryBalance.sku_id == sku_id)
    if location_id is not None:
        stmt = stmt.where(InventoryBalance.location_id == location_id)
    stmt = stmt.order_by(InventoryBalance.id.asc())
    rows = session.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "warehouse_id": row.warehouse_id,
            "sku_id": row.sku_id,
            "location_id": row.location_id,
            "qty_on_hand": _fmt(row.qty_on_hand),
            "qty_frozen": _fmt(row.qty_frozen),
            "qty_available": _fmt(_available(row.qty_on_hand, row.qty_frozen)),
            "version": row.version,
        }
        for row in rows
    ]


def list_ledgers(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    ref_line_id: int | None = None,
    ref_id: int | None = None,
    ref_type: str | None = None,
) -> list[dict]:
    stmt = select(InventoryLedger)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryLedger.warehouse_id == warehouse_id)
    if sku_id is not None:
        stmt = stmt.where(InventoryLedger.sku_id == sku_id)
    if ref_line_id is not None:
        stmt = stmt.where(InventoryLedger.ref_line_id == ref_line_id)
    if ref_id is not None:
        stmt = stmt.where(InventoryLedger.ref_id == ref_id)
    if ref_type is not None:
        stmt = stmt.where(InventoryLedger.ref_type == ref_type)
    stmt = stmt.order_by(InventoryLedger.id.asc())
    rows = session.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "warehouse_id": row.warehouse_id,
            "sku_id": row.sku_id,
            "location_id": row.location_id,
            "change_qty": _fmt(row.change_qty),
            "bal_qty": _fmt(row.bal_qty),
            "ref_type": row.ref_type,
            "ref_id": row.ref_id,
            "ref_line_id": row.ref_line_id,
            "ref_no": row.ref_no,
            "operator_id": row.operator_id,
            "created_at": row.created_at.isoformat(sep=" ", timespec="seconds"),
        }
        for row in rows
    ]
