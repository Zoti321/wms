"""余额 + 库存流水 persistence 与 book_mutation 编排（库存上下文内部 seam）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.inventory.application import alert_evaluator, idempotency_store
from app.inventory.application.types import (
    ADJUST_SCOPE,
    ALLOCATE_SCOPE,
    DEDUCT_SCOPE,
    RELEASE_SCOPE,
    InventoryConflictError,
    InventoryInsufficientError,
    MutationResult,
    available_qty,
    fmt_qty,
)
from app.inventory.infrastructure.models import InventoryBalance, InventoryLedger
from app.shared.metrics import record_inventory_operation
from app.shared.pagination import paginate, paginated_payload

_SCOPE_OPERATION = {
    ALLOCATE_SCOPE: "allocate",
    DEDUCT_SCOPE: "pick",
    RELEASE_SCOPE: "release",
    ADJUST_SCOPE: "adjust",
}


@dataclass(frozen=True)
class BookMutationContext:
    scope: str
    idempotency_key: str
    warehouse_id: int
    sku_id: int
    location_id: int
    create_if_missing: bool
    ref_type: str
    ref_id: int
    ref_line_id: int | None
    ref_no: str
    operator_id: int


ApplyFn = Callable[[Session, InventoryBalance | None], tuple[InventoryBalance, Decimal]]


def get_balance(
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


def mutation_result(balance: InventoryBalance, ledger_id: int) -> MutationResult:
    return MutationResult(
        inventory_id=balance.id,
        qty_on_hand=fmt_qty(balance.qty_on_hand),
        qty_frozen=fmt_qty(balance.qty_frozen),
        qty_available=fmt_qty(available_qty(balance.qty_on_hand, balance.qty_frozen)),
        version=balance.version,
        ledger_id=ledger_id,
        replayed=False,
    )


def write_ledger(
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


def optimistic_update(
    session: Session,
    *,
    balance_id: int,
    expected_version: int,
    values: dict,
    extra_where: tuple = (),
) -> None:
    result = session.execute(
        update(InventoryBalance)
        .where(
            InventoryBalance.id == balance_id,
            InventoryBalance.version == expected_version,
            *extra_where,
        )
        .values(**values)
    )
    if result.rowcount != 1:
        raise InventoryConflictError("库存版本冲突，请重试")


def book_mutation(
    session: Session,
    ctx: BookMutationContext,
    apply: ApplyFn,
) -> MutationResult:
    """幂等 → 余额变更 → 流水 → 幂等落库 → 预警；各 mutation 只提供 apply 逻辑。"""
    operation = _SCOPE_OPERATION.get(ctx.scope)
    try:
        replay = idempotency_store.try_replay(
            session, scope=ctx.scope, key=ctx.idempotency_key
        )
        if replay is not None:
            if operation is not None:
                record_inventory_operation(operation, "success")
            return replay

        balance = get_balance(
            session,
            warehouse_id=ctx.warehouse_id,
            sku_id=ctx.sku_id,
            location_id=ctx.location_id,
            create_if_missing=ctx.create_if_missing,
        )
        balance, change_qty = apply(session, balance)

        ledger = write_ledger(
            session,
            balance=balance,
            change_qty=change_qty,
            ref_type=ctx.ref_type,
            ref_id=ctx.ref_id,
            ref_line_id=ctx.ref_line_id,
            ref_no=ctx.ref_no,
            operator_id=ctx.operator_id,
        )
        mutation = mutation_result(balance, ledger.id)
        idempotency_store.store_mutation(
            session,
            scope=ctx.scope,
            key=ctx.idempotency_key,
            result=mutation,
        )
        alert_evaluator.evaluate(
            session, warehouse_id=ctx.warehouse_id, sku_id=ctx.sku_id
        )
        session.flush()
        if operation is not None:
            record_inventory_operation(operation, "success")
        return mutation
    except InventoryInsufficientError:
        if operation is not None:
            record_inventory_operation(operation, "insufficient")
        raise
    except InventoryConflictError:
        if operation is not None:
            record_inventory_operation(operation, "conflict")
        raise
    except Exception:
        if operation is not None:
            record_inventory_operation(operation, "error")
        raise


def list_balances(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    location_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = select(InventoryBalance)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryBalance.warehouse_id == warehouse_id)
    if sku_id is not None:
        stmt = stmt.where(InventoryBalance.sku_id == sku_id)
    if location_id is not None:
        stmt = stmt.where(InventoryBalance.location_id == location_id)
    stmt = stmt.order_by(
        InventoryBalance.warehouse_id.asc(),
        InventoryBalance.sku_id.asc(),
        InventoryBalance.location_id.asc(),
    )
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [
            {
                "id": row.id,
                "warehouse_id": row.warehouse_id,
                "sku_id": row.sku_id,
                "location_id": row.location_id,
                "qty_on_hand": fmt_qty(row.qty_on_hand),
                "qty_frozen": fmt_qty(row.qty_frozen),
                "qty_available": fmt_qty(available_qty(row.qty_on_hand, row.qty_frozen)),
                "version": row.version,
            }
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_ledgers(
    session: Session,
    *,
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    ref_line_id: int | None = None,
    ref_id: int | None = None,
    ref_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
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
    stmt = stmt.order_by(InventoryLedger.created_at.desc(), InventoryLedger.id.desc())
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [
            {
                "id": row.id,
                "warehouse_id": row.warehouse_id,
                "sku_id": row.sku_id,
                "location_id": row.location_id,
                "change_qty": fmt_qty(row.change_qty),
                "bal_qty": fmt_qty(row.bal_qty),
                "ref_type": row.ref_type,
                "ref_id": row.ref_id,
                "ref_line_id": row.ref_line_id,
                "ref_no": row.ref_no,
                "operator_id": row.operator_id,
                "created_at": row.created_at.isoformat(sep=" ", timespec="seconds"),
            }
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
