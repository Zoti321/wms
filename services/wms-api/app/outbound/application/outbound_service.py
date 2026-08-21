"""出库用例：状态机与分配/拣货/取消（经库存端口，不直写库存表）。"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.catalog.domain.status import ActiveStatus
from app.catalog.infrastructure.models import Location, Sku, Warehouse
from app.inventory.application import inventory_service as inv
from app.inventory.application.lock import is_location_locked
from app.outbound.domain.status import (
    APPROVE_ALLOWED,
    CANCEL_RELEASE_STATUSES,
    EDITABLE_STATUSES,
    ORDER_TYPES,
    PICK_ALLOWED,
    STATUS_APPROVED,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_DRAFT,
    STATUS_PENDING,
    STATUS_PICKING,
    TERMINAL_STATUSES,
)
from app.outbound.infrastructure.models import (
    OutboundOrder,
    OutboundOrderLine,
    PickRecord,
)

APPROVE_SCOPE = "outbound.approve"
PICK_SCOPE = "outbound.pick"
CANCEL_SCOPE = "outbound.cancel"


class OutboundError(Exception):
    """出库业务错误。"""


class OutboundNotFoundError(OutboundError):
    pass


class OutboundConflictError(OutboundError):
    pass


def _fmt(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def _order_to_dict(order: OutboundOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "warehouse_id": order.warehouse_id,
        "order_type": order.order_type,
        "status": order.status,
        "customer_id": order.customer_id,
        "remark": order.remark,
        "created_by": order.created_by,
        "lines": [
            {
                "id": line.id,
                "sku_id": line.sku_id,
                "planned_qty": _fmt(line.planned_qty),
                "allocated_qty": _fmt(line.allocated_qty),
                "picked_qty": _fmt(line.picked_qty),
                "location_id": line.location_id,
            }
            for line in order.lines
        ],
    }


def _get_order(session: Session, order_id: int) -> OutboundOrder:
    order = session.scalars(
        select(OutboundOrder)
        .options(joinedload(OutboundOrder.lines))
        .where(OutboundOrder.id == order_id)
    ).first()
    if order is None:
        raise OutboundNotFoundError("出库单不存在")
    return order


def create_order(
    session: Session,
    *,
    warehouse_id: int,
    order_type: str,
    lines: list[dict],
    created_by: int,
    customer_id: int | None = None,
    remark: str | None = None,
    order_no: str | None = None,
) -> dict:
    if order_type not in ORDER_TYPES:
        raise OutboundError("无效的出库类型")
    if not lines:
        raise OutboundError("至少一行出库单行")
    wh = session.get(Warehouse, warehouse_id)
    if wh is None or wh.status != ActiveStatus.ACTIVE:
        raise OutboundError("仓库不可用")

    order = OutboundOrder(
        order_no=order_no or f"OUT-{uuid4().hex[:12].upper()}",
        warehouse_id=warehouse_id,
        order_type=order_type,
        status=STATUS_DRAFT,
        customer_id=customer_id,
        remark=remark,
        created_by=created_by,
    )
    for item in lines:
        sku = session.get(Sku, item["sku_id"])
        if sku is None or sku.status != ActiveStatus.ACTIVE:
            raise OutboundError(f"SKU 不可用: {item['sku_id']}")
        planned = Decimal(str(item["planned_qty"]))
        if planned <= 0:
            raise OutboundError("计划数量必须大于 0")
        order.lines.append(
            OutboundOrderLine(sku_id=item["sku_id"], planned_qty=planned)
        )
    session.add(order)
    session.commit()
    session.refresh(order)
    return _order_to_dict(_get_order(session, order.id))


def update_order(
    session: Session,
    order_id: int,
    *,
    lines: list[dict] | None = None,
    customer_id: int | None = None,
    remark: str | None = None,
) -> dict:
    order = _get_order(session, order_id)
    if order.status not in EDITABLE_STATUSES:
        raise OutboundConflictError("仅草稿可编辑")
    if customer_id is not None:
        order.customer_id = customer_id
    if remark is not None:
        order.remark = remark
    if lines is not None:
        if not lines:
            raise OutboundError("至少一行出库单行")
        order.lines.clear()
        session.flush()
        for item in lines:
            sku = session.get(Sku, item["sku_id"])
            if sku is None or sku.status != ActiveStatus.ACTIVE:
                raise OutboundError(f"SKU 不可用: {item['sku_id']}")
            planned = Decimal(str(item["planned_qty"]))
            if planned <= 0:
                raise OutboundError("计划数量必须大于 0")
            order.lines.append(
                OutboundOrderLine(sku_id=item["sku_id"], planned_qty=planned)
            )
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def get_order(session: Session, order_id: int) -> dict:
    return _order_to_dict(_get_order(session, order_id))


def submit_order(session: Session, order_id: int) -> dict:
    order = _get_order(session, order_id)
    if order.status != STATUS_DRAFT:
        raise OutboundConflictError("仅草稿可提交")
    if not order.lines:
        raise OutboundError("至少一行出库单行")
    order.status = STATUS_PENDING
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def approve_order(
    session: Session,
    order_id: int,
    *,
    allocations: list[dict],
    operator_id: int,
    idempotency_key: str,
) -> dict:
    """审核 = 整单分配。任一行可用不足则整单失败、不落任何预留。"""
    replay = inv.load_json_idempotent(
        session, scope=APPROVE_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    order = _get_order(session, order_id)
    if order.status not in APPROVE_ALLOWED:
        raise OutboundConflictError("仅待审核可审核")

    if not allocations:
        raise OutboundError("审核须提供分配库位")

    line_by_id = {line.id: line for line in order.lines}
    if len(allocations) != len(order.lines):
        raise OutboundError("须为每一行指定恰好一个分配库位")
    seen_lines: set[int] = set()
    for item in allocations:
        line_id = item["line_id"]
        if line_id in seen_lines:
            raise OutboundError("同一出库单行不可重复分配")
        seen_lines.add(line_id)
        if line_id not in line_by_id:
            raise OutboundNotFoundError("出库单行不存在")

    # 先校验库位，再在同一事务内逐行 allocate；失败则整单回滚。
    prepared: list[tuple[OutboundOrderLine, Location, Decimal]] = []
    for item in allocations:
        line = line_by_id[item["line_id"]]
        location = session.get(Location, item["location_id"])
        if (
            location is None
            or location.status != ActiveStatus.ACTIVE
            or location.warehouse_id != order.warehouse_id
        ):
            raise OutboundError("库位不可用或不属于本仓库")
        if is_location_locked(session, location.id):
            raise OutboundConflictError("库位已盘点锁定，不可分配")
        prepared.append((line, location, line.planned_qty))

    try:
        for line, location, qty in prepared:
            inv.allocate(
                session,
                warehouse_id=order.warehouse_id,
                sku_id=line.sku_id,
                location_id=location.id,
                qty=qty,
                ref_type=inv.REF_TYPE_ALLOCATE,
                ref_id=order.id,
                ref_line_id=line.id,
                ref_no=order.order_no,
                operator_id=operator_id,
                idempotency_key=f"{idempotency_key}:alloc:{line.id}",
            )
            line.location_id = location.id
            line.allocated_qty = qty
    except inv.InventoryInsufficientError as exc:
        session.rollback()
        raise OutboundError(str(exc)) from exc
    except inv.InventoryConflictError as exc:
        session.rollback()
        raise OutboundConflictError(str(exc)) from exc
    except inv.InventoryError as exc:
        session.rollback()
        raise OutboundConflictError(str(exc)) from exc

    order.status = STATUS_APPROVED
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


def pick(
    session: Session,
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty: Decimal,
    operator_id: int,
    idempotency_key: str,
) -> dict:
    replay = inv.load_json_idempotent(
        session, scope=PICK_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    order = _get_order(session, order_id)
    if order.status not in PICK_ALLOWED:
        raise OutboundConflictError("当前状态不可拣货")

    line = next((ln for ln in order.lines if ln.id == line_id), None)
    if line is None:
        raise OutboundNotFoundError("出库单行不存在")

    if qty <= 0:
        raise OutboundError("拣货数量必须大于 0")
    remaining = line.allocated_qty - line.picked_qty
    if qty > remaining:
        raise OutboundError("拣货数量超过行剩余已分配量")

    if line.location_id is None or location_id != line.location_id:
        raise OutboundError("拣货库位须与审核分配库位一致")

    if is_location_locked(session, location_id):
        raise OutboundConflictError("库位已盘点锁定，不可拣货")

    try:
        deduct_result = inv.deduct(
            session,
            warehouse_id=order.warehouse_id,
            sku_id=line.sku_id,
            location_id=location_id,
            qty=qty,
            ref_type=inv.REF_TYPE_PICK,
            ref_id=order.id,
            ref_line_id=line.id,
            ref_no=order.order_no,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
    except inv.InventoryInsufficientError as exc:
        raise OutboundError(str(exc)) from exc
    except inv.InventoryError as exc:
        raise OutboundConflictError(str(exc)) from exc

    if deduct_result.replayed:
        return {
            "order": _order_to_dict(order),
            "deduct": deduct_result.__dict__,
            "replayed": True,
        }

    record = PickRecord(
        order_id=order.id,
        line_id=line.id,
        location_id=location_id,
        qty=qty,
        operator_id=operator_id,
    )
    session.add(record)
    line.picked_qty = line.picked_qty + qty

    if all(ln.picked_qty >= ln.allocated_qty for ln in order.lines):
        order.status = STATUS_DONE
    else:
        order.status = STATUS_PICKING

    session.flush()
    payload = {
        "order": _order_to_dict(order),
        "pick_record_id": record.id,
        "deduct": deduct_result.__dict__,
        "replayed": False,
    }
    inv.store_json_idempotent(
        session, scope=PICK_SCOPE, idempotency_key=idempotency_key, payload=payload
    )
    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "pick_record_id": record.id,
        "deduct": deduct_result.__dict__,
        "replayed": False,
    }


def cancel_order(
    session: Session,
    order_id: int,
    *,
    operator_id: int,
    idempotency_key: str,
) -> dict:
    """取消未拣：释放预留；已实扣不可抹账。"""
    replay = inv.load_json_idempotent(
        session, scope=CANCEL_SCOPE, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {**replay, "replayed": True}

    order = _get_order(session, order_id)
    if order.status in TERMINAL_STATUSES:
        raise OutboundConflictError("已完成或已取消不可再取消")

    if order.status in CANCEL_RELEASE_STATUSES:
        try:
            for line in order.lines:
                remaining = line.allocated_qty - line.picked_qty
                if remaining <= 0:
                    continue
                if line.location_id is None:
                    raise OutboundConflictError("出库单行缺少分配库位，无法释放")
                inv.release(
                    session,
                    warehouse_id=order.warehouse_id,
                    sku_id=line.sku_id,
                    location_id=line.location_id,
                    qty=remaining,
                    ref_type=inv.REF_TYPE_RELEASE,
                    ref_id=order.id,
                    ref_line_id=line.id,
                    ref_no=order.order_no,
                    operator_id=operator_id,
                    idempotency_key=f"{idempotency_key}:release:{line.id}",
                )
                line.allocated_qty = line.picked_qty
        except inv.InventoryInsufficientError as exc:
            session.rollback()
            raise OutboundError(str(exc)) from exc
        except inv.InventoryError as exc:
            session.rollback()
            raise OutboundConflictError(str(exc)) from exc

    has_picked = any(line.picked_qty > 0 for line in order.lines)
    # 已有实扣 → 已完成（保留已出库）；无实扣 → 已取消。纠错走退货入库。
    order.status = STATUS_DONE if has_picked else STATUS_CANCELLED
    note = None
    if has_picked:
        note = "已实扣数量已保留，不可靠取消抹账；纠错请走退货入库"
    payload = {
        "order": _order_to_dict(order),
        "note": note,
        "replayed": False,
    }
    inv.store_json_idempotent(
        session,
        scope=CANCEL_SCOPE,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "note": note,
        "replayed": False,
    }
