"""盘点用例：生效加锁、实盘录入、审核调账释锁、取消释锁（经库存端口，不直写库存表）。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.catalog.domain.status import ActiveStatus
from app.catalog.infrastructure.models import Location, Warehouse
from app.inventory.application import inventory_service as inv
from app.inventory.application import lock as lock_port
from app.platform.domain.permissions import PERM_STOCKTAKE_APPROVE, has_permission
from app.shared.pagination import MAX_PAGE_SIZE
from app.stocktake.domain.status import (
    APPROVE_ALLOWED,
    CANCEL_ALLOWED,
    EDITABLE_STATUSES,
    LOCK_REF_TYPE,
    STATUS_APPROVED,
    STATUS_CANCELLED,
    STATUS_COUNTING,
    TERMINAL_STATUSES,
)
from app.shared.pagination import paginate, paginated_payload
from app.stocktake.infrastructure.models import StocktakeLine, StocktakeOrder

CREATE_SCOPE = "stocktake.create"
APPROVE_SCOPE = "stocktake.approve"
CANCEL_SCOPE = "stocktake.cancel"


class StocktakeError(Exception):
    """盘点业务错误。"""


class StocktakeNotFoundError(StocktakeError):
    pass


class StocktakeConflictError(StocktakeError):
    pass


class StocktakeForbiddenError(StocktakeError):
    """角色不足（如非主管审核）。"""


def _fmt(qty: Decimal | None) -> str | None:
    if qty is None:
        return None
    return f"{qty.quantize(Decimal('0.001'))}"


def _fmt_dt(value: datetime) -> str:
    return value.isoformat(sep=" ", timespec="seconds")


def _order_list_item(order: StocktakeOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "warehouse_id": order.warehouse_id,
        "status": order.status,
        "created_at": _fmt_dt(order.created_at),
    }


def _diff(book_qty: Decimal, counted_qty: Decimal | None) -> str | None:
    if counted_qty is None:
        return None
    return _fmt(counted_qty - book_qty)


def _order_to_dict(order: StocktakeOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "warehouse_id": order.warehouse_id,
        "zone": order.zone,
        "status": order.status,
        "remark": order.remark,
        "created_by": order.created_by,
        "created_at": _fmt_dt(order.created_at),
        "approved_by": order.approved_by,
        "lines": [
            {
                "id": line.id,
                "location_id": line.location_id,
                "sku_id": line.sku_id,
                "book_qty": _fmt(line.book_qty),
                "counted_qty": _fmt(line.counted_qty),
                "diff_qty": _diff(line.book_qty, line.counted_qty),
            }
            for line in order.lines
        ],
    }


def _get_order(session: Session, order_id: int) -> StocktakeOrder:
    order = session.scalars(
        select(StocktakeOrder)
        .options(joinedload(StocktakeOrder.lines))
        .where(StocktakeOrder.id == order_id)
    ).first()
    if order is None:
        raise StocktakeNotFoundError("盘点单不存在")
    return order


def get_order(session: Session, order_id: int) -> dict:
    return _order_to_dict(_get_order(session, order_id))


def list_orders(
    session: Session,
    *,
    warehouse_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = select(StocktakeOrder)
    if warehouse_id is not None:
        stmt = stmt.where(StocktakeOrder.warehouse_id == warehouse_id)
    if status is not None:
        stmt = stmt.where(StocktakeOrder.status == status)
    stmt = stmt.order_by(StocktakeOrder.created_at.desc(), StocktakeOrder.id.desc())
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [_order_list_item(order) for order in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_order(
    session: Session,
    *,
    warehouse_id: int,
    created_by: int,
    zone: str | None = None,
    remark: str | None = None,
    order_no: str | None = None,
    idempotency_key: str,
) -> dict:
    replay = inv.load_json_idempotent(
        session, scope=CREATE_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    wh = session.get(Warehouse, warehouse_id)
    if wh is None or wh.status != ActiveStatus.ACTIVE:
        raise StocktakeError("仓库不可用")

    loc_stmt = select(Location).where(
        Location.warehouse_id == warehouse_id,
        Location.status == ActiveStatus.ACTIVE,
    )
    if zone is not None:
        loc_stmt = loc_stmt.where(Location.zone == zone)
    locations = list(session.scalars(loc_stmt).all())
    if not locations:
        raise StocktakeError("盘点范围内无可用库位")

    location_ids = [loc.id for loc in locations]
    all_balances: list[dict] = []
    page = 1
    while True:
        payload = inv.list_balances(
            session, warehouse_id=warehouse_id, page=page, page_size=MAX_PAGE_SIZE
        )
        all_balances.extend(payload["items"])
        if page * MAX_PAGE_SIZE >= payload["total"]:
            break
        page += 1
    balances = [b for b in all_balances if b["location_id"] in set(location_ids)]

    order = StocktakeOrder(
        order_no=order_no or f"ST-{uuid4().hex[:12].upper()}",
        warehouse_id=warehouse_id,
        zone=zone,
        status=STATUS_COUNTING,
        remark=remark,
        created_by=created_by,
    )
    session.add(order)
    session.flush()

    for bal in balances:
        session.add(
            StocktakeLine(
                order_id=order.id,
                location_id=bal["location_id"],
                sku_id=bal["sku_id"],
                book_qty=Decimal(bal["qty_on_hand"]),
                counted_qty=None,
            )
        )

    try:
        lock_port.acquire_location_locks(
            session,
            location_ids=location_ids,
            ref_type=LOCK_REF_TYPE,
            ref_id=order.id,
        )
    except lock_port.LocationLockConflictError as exc:
        raise StocktakeConflictError("范围内库位已有盘点锁，无法发起") from exc

    session.flush()
    payload = {"order": _order_to_dict(_get_order(session, order.id)), "replayed": False}
    inv.store_json_idempotent(
        session,
        scope=CREATE_SCOPE,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "replayed": False,
    }


def record_counts(
    session: Session,
    order_id: int,
    *,
    lines: list[dict],
) -> dict:
    order = _get_order(session, order_id)
    if order.status not in EDITABLE_STATUSES:
        raise StocktakeConflictError("已完成或已取消的盘点单不可再编辑")
    if not lines:
        raise StocktakeError("至少一行实盘数量")

    line_by_id = {ln.id: ln for ln in order.lines}
    for item in lines:
        line = line_by_id.get(item["line_id"])
        if line is None:
            raise StocktakeNotFoundError("盘点单行不存在")
        qty = Decimal(item["counted_qty"])
        if qty < 0:
            raise StocktakeError("实盘数量不能为负")
        line.counted_qty = qty

    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def approve_order(
    session: Session,
    order_id: int,
    *,
    operator_id: int,
    role_code: str,
    idempotency_key: str,
) -> dict:
    if not has_permission(role_code, PERM_STOCKTAKE_APPROVE):
        raise StocktakeForbiddenError("仅仓库主管可审核盘点")

    replay = inv.load_json_idempotent(
        session, scope=APPROVE_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    order = _get_order(session, order_id)
    if order.status not in APPROVE_ALLOWED:
        raise StocktakeConflictError("当前状态不可审核")

    for line in order.lines:
        if line.counted_qty is None:
            raise StocktakeError("存在未录入实盘的行，不可审核")

    try:
        for line in order.lines:
            delta = line.counted_qty - line.book_qty
            if delta == 0:
                continue
            inv.adjust(
                session,
                warehouse_id=order.warehouse_id,
                sku_id=line.sku_id,
                location_id=line.location_id,
                qty=delta,
                ref_type=inv.REF_TYPE_STOCKTAKE,
                ref_id=order.id,
                ref_line_id=line.id,
                ref_no=order.order_no,
                operator_id=operator_id,
                idempotency_key=f"{idempotency_key}:adj:{line.id}",
            )
    except inv.InventoryInsufficientError as exc:
        session.rollback()
        raise StocktakeError(str(exc)) from exc
    except inv.InventoryConflictError as exc:
        session.rollback()
        raise StocktakeConflictError(str(exc)) from exc
    except inv.InventoryError as exc:
        session.rollback()
        raise StocktakeError(str(exc)) from exc

    lock_port.release_location_locks(
        session, ref_type=LOCK_REF_TYPE, ref_id=order.id
    )
    order.status = STATUS_APPROVED
    order.approved_by = operator_id
    payload = {"order": _order_to_dict(order), "replayed": False}
    inv.store_json_idempotent(
        session,
        scope=APPROVE_SCOPE,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "replayed": False,
    }


def cancel_order(
    session: Session,
    order_id: int,
    *,
    operator_id: int,
    idempotency_key: str,
    cancel_reason_code: str | None = None,
) -> dict:
    from app.shared.cancel_reason import (
        append_cancel_reason_to_remark,
        resolve_cancel_reason_name,
    )

    reason_name = resolve_cancel_reason_name(session, cancel_reason_code)
    replay = inv.load_json_idempotent(
        session, scope=CANCEL_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    order = _get_order(session, order_id)
    if order.status in TERMINAL_STATUSES:
        raise StocktakeConflictError("已完成或已取消不可再取消")
    if order.status not in CANCEL_ALLOWED:
        raise StocktakeConflictError("当前状态不可取消")

    lock_port.release_location_locks(
        session, ref_type=LOCK_REF_TYPE, ref_id=order.id
    )
    if reason_name is not None:
        order.remark = append_cancel_reason_to_remark(order.remark, reason_name)
    order.status = STATUS_CANCELLED
    _ = operator_id  # 操作日志归 M6
    payload = {"order": _order_to_dict(order), "replayed": False}
    inv.store_json_idempotent(
        session,
        scope=CANCEL_SCOPE,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "replayed": False,
    }
