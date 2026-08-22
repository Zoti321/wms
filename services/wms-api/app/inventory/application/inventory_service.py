"""库存记账端口：increase / allocate / deduct / release / adjust；余额维度仓库+SKU+库位。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.inventory.application import alert_evaluator, idempotency_store, ledger_port
from app.inventory.application.ledger_port import BookMutationContext
from app.inventory.application.types import (
    ADJUST_SCOPE,
    ALERT_STATUS_CLEARED,
    ALERT_STATUS_OPEN,
    ALLOCATE_SCOPE,
    DEDUCT_SCOPE,
    INCREASE_SCOPE,
    REF_TYPE_ALLOCATE,
    REF_TYPE_PICK,
    REF_TYPE_PUTAWAY,
    REF_TYPE_RELEASE,
    REF_TYPE_STOCKTAKE,
    RELEASE_SCOPE,
    IncreaseResult,
    InventoryConflictError,
    InventoryError,
    InventoryInsufficientError,
    MutationResult,
    available_qty,
)
from app.inventory.infrastructure.models import InventoryBalance

__all__ = [
    "ALERT_STATUS_CLEARED",
    "ALERT_STATUS_OPEN",
    "ADJUST_SCOPE",
    "ALLOCATE_SCOPE",
    "DEDUCT_SCOPE",
    "INCREASE_SCOPE",
    "IncreaseResult",
    "InventoryConflictError",
    "InventoryError",
    "InventoryInsufficientError",
    "MutationResult",
    "REF_TYPE_ALLOCATE",
    "REF_TYPE_PICK",
    "REF_TYPE_PUTAWAY",
    "REF_TYPE_RELEASE",
    "REF_TYPE_STOCKTAKE",
    "RELEASE_SCOPE",
    "adjust",
    "allocate",
    "deduct",
    "increase",
    "list_alerts",
    "list_balances",
    "list_ledgers",
    "load_adjust_idempotent",
    "load_allocate_idempotent",
    "load_deduct_idempotent",
    "load_increase_idempotent",
    "load_json_idempotent",
    "load_release_idempotent",
    "release",
    "store_json_idempotent",
]


def _mutation_ctx(
    *,
    scope: str,
    idempotency_key: str,
    warehouse_id: int,
    sku_id: int,
    location_id: int,
    create_if_missing: bool,
    ref_type: str,
    ref_id: int,
    ref_line_id: int | None,
    ref_no: str,
    operator_id: int,
) -> BookMutationContext:
    return BookMutationContext(
        scope=scope,
        idempotency_key=idempotency_key,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        create_if_missing=create_if_missing,
        ref_type=ref_type,
        ref_id=ref_id,
        ref_line_id=ref_line_id,
        ref_no=ref_no,
        operator_id=operator_id,
    )


def load_increase_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = idempotency_store.load_mutation(
        session, scope=INCREASE_SCOPE, key=idempotency_key
    )
    return idempotency_store.replay(existing) if existing is not None else None


def load_allocate_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = idempotency_store.load_mutation(
        session, scope=ALLOCATE_SCOPE, key=idempotency_key
    )
    return idempotency_store.replay(existing) if existing is not None else None


def load_deduct_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = idempotency_store.load_mutation(
        session, scope=DEDUCT_SCOPE, key=idempotency_key
    )
    return idempotency_store.replay(existing) if existing is not None else None


def load_release_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = idempotency_store.load_mutation(
        session, scope=RELEASE_SCOPE, key=idempotency_key
    )
    return idempotency_store.replay(existing) if existing is not None else None


def load_adjust_idempotent(
    session: Session, *, idempotency_key: str
) -> MutationResult | None:
    existing = idempotency_store.load_mutation(
        session, scope=ADJUST_SCOPE, key=idempotency_key
    )
    return idempotency_store.replay(existing) if existing is not None else None


def load_json_idempotent(
    session: Session, *, scope: str, idempotency_key: str
) -> dict | None:
    return idempotency_store.load_json(
        session, scope=scope, idempotency_key=idempotency_key
    )


def store_json_idempotent(
    session: Session, *, scope: str, idempotency_key: str, payload: dict
) -> None:
    idempotency_store.store_json(
        session, scope=scope, idempotency_key=idempotency_key, payload=payload
    )


def list_alerts(
    session: Session,
    *,
    warehouse_id: int | None = None,
) -> list[dict]:
    return alert_evaluator.list_alerts(session, warehouse_id=warehouse_id)


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

    def apply(session: Session, balance) -> tuple:
        assert balance is not None
        expected_version = balance.version
        new_on_hand = balance.qty_on_hand + qty
        ledger_port.optimistic_update(
            session,
            balance_id=balance.id,
            expected_version=expected_version,
            values={"qty_on_hand": new_on_hand, "version": expected_version + 1},
        )
        session.refresh(balance)
        return balance, qty

    return ledger_port.book_mutation(
        session,
        _mutation_ctx(
            scope=INCREASE_SCOPE,
            idempotency_key=idempotency_key,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            create_if_missing=True,
            ref_type=ref_type,
            ref_id=ref_id,
            ref_line_id=ref_line_id,
            ref_no=ref_no,
            operator_id=operator_id,
        ),
        apply,
    )


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

    def apply(session: Session, balance) -> tuple:
        if balance is None:
            raise InventoryInsufficientError("库存可用不足，无法分配")
        if available_qty(balance.qty_on_hand, balance.qty_frozen) < qty:
            raise InventoryInsufficientError("库存可用不足，无法分配")

        expected_version = balance.version
        new_frozen = balance.qty_frozen + qty
        ledger_port.optimistic_update(
            session,
            balance_id=balance.id,
            expected_version=expected_version,
            values={"qty_frozen": new_frozen, "version": expected_version + 1},
            extra_where=(
                (InventoryBalance.qty_on_hand - InventoryBalance.qty_frozen) >= qty,
            ),
        )
        session.refresh(balance)
        return balance, Decimal("0")

    return ledger_port.book_mutation(
        session,
        _mutation_ctx(
            scope=ALLOCATE_SCOPE,
            idempotency_key=idempotency_key,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            create_if_missing=False,
            ref_type=ref_type,
            ref_id=ref_id,
            ref_line_id=ref_line_id,
            ref_no=ref_no,
            operator_id=operator_id,
        ),
        apply,
    )


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

    def apply(session: Session, balance) -> tuple:
        if balance is None or balance.qty_frozen < qty or balance.qty_on_hand < qty:
            raise InventoryInsufficientError("冻结数量不足，无法实扣")

        expected_version = balance.version
        ledger_port.optimistic_update(
            session,
            balance_id=balance.id,
            expected_version=expected_version,
            values={
                "qty_frozen": balance.qty_frozen - qty,
                "qty_on_hand": balance.qty_on_hand - qty,
                "version": expected_version + 1,
            },
            extra_where=(
                InventoryBalance.qty_frozen >= qty,
                InventoryBalance.qty_on_hand >= qty,
            ),
        )
        session.refresh(balance)
        return balance, -qty

    return ledger_port.book_mutation(
        session,
        _mutation_ctx(
            scope=DEDUCT_SCOPE,
            idempotency_key=idempotency_key,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            create_if_missing=False,
            ref_type=ref_type,
            ref_id=ref_id,
            ref_line_id=ref_line_id,
            ref_no=ref_no,
            operator_id=operator_id,
        ),
        apply,
    )


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

    def apply(session: Session, balance) -> tuple:
        if balance is None or balance.qty_frozen < qty:
            raise InventoryInsufficientError("冻结数量不足，无法释放预留")

        expected_version = balance.version
        ledger_port.optimistic_update(
            session,
            balance_id=balance.id,
            expected_version=expected_version,
            values={
                "qty_frozen": balance.qty_frozen - qty,
                "version": expected_version + 1,
            },
            extra_where=(InventoryBalance.qty_frozen >= qty,),
        )
        session.refresh(balance)
        return balance, Decimal("0")

    return ledger_port.book_mutation(
        session,
        _mutation_ctx(
            scope=RELEASE_SCOPE,
            idempotency_key=idempotency_key,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            create_if_missing=False,
            ref_type=ref_type,
            ref_id=ref_id,
            ref_line_id=ref_line_id,
            ref_no=ref_no,
            operator_id=operator_id,
        ),
        apply,
    )


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

    def apply(session: Session, balance) -> tuple:
        if balance is None:
            raise InventoryInsufficientError("库存在库不足，无法盘亏")

        new_on_hand = balance.qty_on_hand + qty
        if new_on_hand < 0 or new_on_hand < balance.qty_frozen:
            raise InventoryInsufficientError("库存在库不足，无法盘亏")

        expected_version = balance.version
        ledger_port.optimistic_update(
            session,
            balance_id=balance.id,
            expected_version=expected_version,
            values={"qty_on_hand": new_on_hand, "version": expected_version + 1},
            extra_where=(
                (InventoryBalance.qty_on_hand + qty) >= 0,
                (InventoryBalance.qty_on_hand + qty) >= InventoryBalance.qty_frozen,
            ),
        )
        session.refresh(balance)
        return balance, qty

    return ledger_port.book_mutation(
        session,
        _mutation_ctx(
            scope=ADJUST_SCOPE,
            idempotency_key=idempotency_key,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            create_if_missing=qty > 0,
            ref_type=ref_type,
            ref_id=ref_id,
            ref_line_id=ref_line_id,
            ref_no=ref_no,
            operator_id=operator_id,
        ),
        apply,
    )


def list_balances(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    location_id: int | None = None,
) -> list[dict]:
    return ledger_port.list_balances(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
    )


def list_ledgers(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    ref_line_id: int | None = None,
    ref_id: int | None = None,
    ref_type: str | None = None,
) -> list[dict]:
    return ledger_port.list_ledgers(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        ref_line_id=ref_line_id,
        ref_id=ref_id,
        ref_type=ref_type,
    )
