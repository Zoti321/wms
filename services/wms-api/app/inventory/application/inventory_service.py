"""库存记账端口：increase / allocate / deduct / release / adjust；余额维度仓库+SKU+库位。"""

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


def _fmt(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def _available(on_hand: Decimal, frozen: Decimal) -> Decimal:
    return on_hand - frozen


def _load_idempotent(
    session: Session, *, scope: str, key: str
) -> MutationResult | None:
    row = session.scalars(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == key,
        )
    ).first()
    if row is None:
        return None
    payload = json.loads(row.response_json)
    return MutationResult(**payload)


def _store_idempotent(
    session: Session, *, scope: str, key: str, result: MutationResult
) -> None:
    session.add(
        IdempotencyRecord(
            scope=scope,
            idempotency_key=key,
            response_json=json.dumps(asdict(result)),
        )
    )


def _replay(result: MutationResult) -> MutationResult:
    return MutationResult(
        inventory_id=result.inventory_id,
        qty_on_hand=result.qty_on_hand,
        qty_frozen=result.qty_frozen,
        qty_available=result.qty_available,
        version=result.version,
        ledger_id=result.ledger_id,
        replayed=True,
    )


def _get_balance(
    session: Session,
    *,
    warehouse_id: int,
    sku_id: int,
    location_id: int,
    create_if_missing: bool,
) -> InventoryBalance | None:
    balance = session.scalars(
        select(InventoryBalance).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.sku_id == sku_id,
            InventoryBalance.location_id == location_id,
        )
    ).first()
    if balance is not None:
        return balance
    if not create_if_missing:
        return None
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
    return balance


def _mutation_result(balance: InventoryBalance, ledger_id: int) -> MutationResult:
    return MutationResult(
        inventory_id=balance.id,
        qty_on_hand=_fmt(balance.qty_on_hand),
        qty_frozen=_fmt(balance.qty_frozen),
        qty_available=_fmt(_available(balance.qty_on_hand, balance.qty_frozen)),
        version=balance.version,
        ledger_id=ledger_id,
        replayed=False,
    )


def _write_ledger(
    session: Session,
    *,
    balance: InventoryBalance,
    change_qty: Decimal,
    ref_type: str,
    ref_id: int,
    ref_line_id: int | None,
    ref_no: str,
    operator_id: int,
) -> InventoryLedger:
    ledger = InventoryLedger(
        warehouse_id=balance.warehouse_id,
        sku_id=balance.sku_id,
        location_id=balance.location_id,
        change_qty=change_qty,
        bal_qty=balance.qty_on_hand,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    session.add(ledger)
    session.flush()
    return ledger


def load_increase_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = _load_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key
    )
    return _replay(existing) if existing is not None else None


def load_allocate_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = _load_idempotent(
        session, scope=ALLOCATE_SCOPE, key=idempotency_key
    )
    return _replay(existing) if existing is not None else None


def load_deduct_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = _load_idempotent(session, scope=DEDUCT_SCOPE, key=idempotency_key)
    return _replay(existing) if existing is not None else None


def load_release_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = _load_idempotent(
        session, scope=RELEASE_SCOPE, key=idempotency_key
    )
    return _replay(existing) if existing is not None else None


def load_adjust_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = _load_idempotent(session, scope=ADJUST_SCOPE, key=idempotency_key)
    return _replay(existing) if existing is not None else None


def load_json_idempotent(
    session: Session, *, scope: str, idempotency_key: str
) -> dict | None:
    """供入/出库适配器复用同一幂等表（不直连基础设施模型）。"""
    row = session.scalars(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
    ).first()
    if row is None:
        return None
    return json.loads(row.response_json)


def store_json_idempotent(
    session: Session, *, scope: str, idempotency_key: str, payload: dict
) -> None:
    session.add(
        IdempotencyRecord(
            scope=scope,
            idempotency_key=idempotency_key,
            response_json=json.dumps(payload),
        )
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
) -> MutationResult:
    """增加在库数量并写流水。同一幂等键重复调用返回首次结果。"""
    if qty <= 0:
        raise InventoryError("上架数量必须大于 0")

    existing = _load_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key
    )
    if existing is not None:
        return _replay(existing)

    balance = _get_balance(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=True,
    )
    assert balance is not None

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
    ledger = _write_ledger(
        session,
        balance=balance,
        change_qty=qty,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    mutation = _mutation_result(balance, ledger.id)
    _store_idempotent(
        session, scope=INCREASE_SCOPE, key=idempotency_key, result=mutation
    )
    session.flush()
    return mutation


def allocate(
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
) -> MutationResult:
    """可用→冻结。可用不足整笔失败；在库不变。"""
    if qty <= 0:
        raise InventoryError("分配数量必须大于 0")

    existing = _load_idempotent(
        session, scope=ALLOCATE_SCOPE, key=idempotency_key
    )
    if existing is not None:
        return _replay(existing)

    balance = _get_balance(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=False,
    )
    if balance is None:
        raise InventoryInsufficientError("库存可用不足，无法分配")

    if _available(balance.qty_on_hand, balance.qty_frozen) < qty:
        raise InventoryInsufficientError("库存可用不足，无法分配")

    expected_version = balance.version
    new_frozen = balance.qty_frozen + qty
    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance.id,
            InventoryBalance.version == expected_version,
            (InventoryBalance.qty_on_hand - InventoryBalance.qty_frozen) >= qty,
        )
        .values(qty_frozen=new_frozen, version=expected_version + 1)
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")

    session.refresh(balance)
    ledger = _write_ledger(
        session,
        balance=balance,
        change_qty=Decimal("0"),
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    mutation = _mutation_result(balance, ledger.id)
    _store_idempotent(
        session, scope=ALLOCATE_SCOPE, key=idempotency_key, result=mutation
    )
    session.flush()
    return mutation


def deduct(
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
) -> MutationResult:
    """实扣：冻结与在库同减。"""
    if qty <= 0:
        raise InventoryError("实扣数量必须大于 0")

    existing = _load_idempotent(session, scope=DEDUCT_SCOPE, key=idempotency_key)
    if existing is not None:
        return _replay(existing)

    balance = _get_balance(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=False,
    )
    if balance is None or balance.qty_frozen < qty or balance.qty_on_hand < qty:
        raise InventoryInsufficientError("冻结数量不足，无法实扣")

    expected_version = balance.version
    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance.id,
            InventoryBalance.version == expected_version,
            InventoryBalance.qty_frozen >= qty,
            InventoryBalance.qty_on_hand >= qty,
        )
        .values(
            qty_frozen=balance.qty_frozen - qty,
            qty_on_hand=balance.qty_on_hand - qty,
            version=expected_version + 1,
        )
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")

    session.refresh(balance)
    ledger = _write_ledger(
        session,
        balance=balance,
        change_qty=-qty,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    mutation = _mutation_result(balance, ledger.id)
    _store_idempotent(
        session, scope=DEDUCT_SCOPE, key=idempotency_key, result=mutation
    )
    session.flush()
    return mutation


def release(
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
) -> MutationResult:
    """释放预留：仅减冻结，在库不变。"""
    if qty <= 0:
        raise InventoryError("释放数量必须大于 0")

    existing = _load_idempotent(
        session, scope=RELEASE_SCOPE, key=idempotency_key
    )
    if existing is not None:
        return _replay(existing)

    balance = _get_balance(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=False,
    )
    if balance is None or balance.qty_frozen < qty:
        raise InventoryInsufficientError("冻结数量不足，无法释放预留")

    expected_version = balance.version
    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance.id,
            InventoryBalance.version == expected_version,
            InventoryBalance.qty_frozen >= qty,
        )
        .values(
            qty_frozen=balance.qty_frozen - qty,
            version=expected_version + 1,
        )
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")

    session.refresh(balance)
    ledger = _write_ledger(
        session,
        balance=balance,
        change_qty=Decimal("0"),
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    mutation = _mutation_result(balance, ledger.id)
    _store_idempotent(
        session, scope=RELEASE_SCOPE, key=idempotency_key, result=mutation
    )
    session.flush()
    return mutation


def adjust(
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
) -> MutationResult:
    """盘盈/盘亏调账：qty 为正增在库、为负减在库；不得导致在库低于冻结或为负。"""
    if qty == 0:
        raise InventoryError("调整数量不能为 0")

    existing = _load_idempotent(session, scope=ADJUST_SCOPE, key=idempotency_key)
    if existing is not None:
        return _replay(existing)

    create_if_missing = qty > 0
    balance = _get_balance(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=create_if_missing,
    )
    if balance is None:
        raise InventoryInsufficientError("库存在库不足，无法盘亏")

    new_on_hand = balance.qty_on_hand + qty
    if new_on_hand < 0 or new_on_hand < balance.qty_frozen:
        raise InventoryInsufficientError("库存在库不足，无法盘亏")

    expected_version = balance.version
    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance.id,
            InventoryBalance.version == expected_version,
            (InventoryBalance.qty_on_hand + qty) >= 0,
            (InventoryBalance.qty_on_hand + qty) >= InventoryBalance.qty_frozen,
        )
        .values(qty_on_hand=new_on_hand, version=expected_version + 1)
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")

    session.refresh(balance)
    ledger = _write_ledger(
        session,
        balance=balance,
        change_qty=qty,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )
    mutation = _mutation_result(balance, ledger.id)
    _store_idempotent(
        session, scope=ADJUST_SCOPE, key=idempotency_key, result=mutation
    )
    session.flush()
    return mutation


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
