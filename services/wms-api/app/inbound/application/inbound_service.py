"""入库用例：状态机与上架（经库存 increase 端口，不直写库存表）。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.catalog.domain.status import ActiveStatus
from app.catalog.infrastructure.models import Location, Sku, Warehouse
from app.inbound.domain.status import (
    EDITABLE_STATUSES,
    ORDER_TYPES,
    PUTAWAY_ALLOWED,
    STATUS_APPROVED,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_DRAFT,
    STATUS_PENDING,
    STATUS_PUTAWAY,
    TERMINAL_STATUSES,
)
from app.inventory.application import inventory_service as inv
from app.inventory.application.lock import is_location_locked
from app.inbound.infrastructure.models import (
    InboundOrder,
    InboundOrderLine,
    PutawayRecord,
)
from app.shared.pagination import paginate, paginated_payload


class InboundError(Exception):
    """入库业务错误。"""


class InboundNotFoundError(InboundError):
    pass


class InboundConflictError(InboundError):
    pass


def _fmt(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def _fmt_dt(value: datetime) -> str:
    return value.isoformat(sep=" ", timespec="seconds")


def _order_list_item(order: InboundOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "warehouse_id": order.warehouse_id,
        "order_type": order.order_type,
        "status": order.status,
        "supplier_id": order.supplier_id,
        "created_at": _fmt_dt(order.created_at),
    }


def _order_to_dict(order: InboundOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "warehouse_id": order.warehouse_id,
        "order_type": order.order_type,
        "status": order.status,
        "supplier_id": order.supplier_id,
        "remark": order.remark,
        "created_by": order.created_by,
        "created_at": _fmt_dt(order.created_at),
        "lines": [
            {
                "id": line.id,
                "sku_id": line.sku_id,
                "planned_qty": _fmt(line.planned_qty),
                "putaway_qty": _fmt(line.putaway_qty),
            }
            for line in order.lines
        ],
    }


def _get_order(session: Session, order_id: int) -> InboundOrder:
    order = session.scalars(
        select(InboundOrder)
        .options(joinedload(InboundOrder.lines))
        .where(InboundOrder.id == order_id)
    ).first()
    if order is None:
        raise InboundNotFoundError("入库单不存在")
    return order


def create_order(
    session: Session,
    *,
    warehouse_id: int,
    order_type: str,
    lines: list[dict],
    created_by: int,
    supplier_id: int | None = None,
    remark: str | None = None,
    order_no: str | None = None,
) -> dict:
    if order_type not in ORDER_TYPES:
        raise InboundError("无效的入库类型")
    if not lines:
        raise InboundError("至少一行入库单行")
    wh = session.get(Warehouse, warehouse_id)
    if wh is None or wh.status != ActiveStatus.ACTIVE:
        raise InboundError("仓库不可用")

    order = InboundOrder(
        order_no=order_no or f"INB-{uuid4().hex[:12].upper()}",
        warehouse_id=warehouse_id,
        order_type=order_type,
        status=STATUS_DRAFT,
        supplier_id=supplier_id,
        remark=remark,
        created_by=created_by,
    )
    for item in lines:
        sku = session.get(Sku, item["sku_id"])
        if sku is None or sku.status != ActiveStatus.ACTIVE:
            raise InboundError(f"SKU 不可用: {item['sku_id']}")
        planned = Decimal(str(item["planned_qty"]))
        if planned <= 0:
            raise InboundError("计划数量必须大于 0")
        order.lines.append(
            InboundOrderLine(sku_id=item["sku_id"], planned_qty=planned)
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
    supplier_id: int | None = None,
    remark: str | None = None,
) -> dict:
    order = _get_order(session, order_id)
    if order.status not in EDITABLE_STATUSES:
        raise InboundConflictError("仅草稿可编辑")
    if supplier_id is not None:
        order.supplier_id = supplier_id
    if remark is not None:
        order.remark = remark
    if lines is not None:
        if not lines:
            raise InboundError("至少一行入库单行")
        order.lines.clear()
        session.flush()
        for item in lines:
            sku = session.get(Sku, item["sku_id"])
            if sku is None or sku.status != ActiveStatus.ACTIVE:
                raise InboundError(f"SKU 不可用: {item['sku_id']}")
            planned = Decimal(str(item["planned_qty"]))
            if planned <= 0:
                raise InboundError("计划数量必须大于 0")
            order.lines.append(
                InboundOrderLine(sku_id=item["sku_id"], planned_qty=planned)
            )
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


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
    stmt = select(InboundOrder)
    if warehouse_id is not None:
        stmt = stmt.where(InboundOrder.warehouse_id == warehouse_id)
    if status is not None:
        stmt = stmt.where(InboundOrder.status == status)
    stmt = stmt.order_by(InboundOrder.created_at.desc(), InboundOrder.id.desc())
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [_order_list_item(order) for order in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def submit_order(session: Session, order_id: int) -> dict:
    order = _get_order(session, order_id)
    if order.status != STATUS_DRAFT:
        raise InboundConflictError("仅草稿可提交")
    if not order.lines:
        raise InboundError("至少一行入库单行")
    order.status = STATUS_PENDING
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def approve_order(session: Session, order_id: int) -> dict:
    order = _get_order(session, order_id)
    if order.status != STATUS_PENDING:
        raise InboundConflictError("仅待审核可审核")
    order.status = STATUS_APPROVED
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def cancel_order(session: Session, order_id: int) -> dict:
    order = _get_order(session, order_id)
    if order.status in TERMINAL_STATUSES:
        raise InboundConflictError("已完成或已取消不可再取消")
    if any(line.putaway_qty > 0 for line in order.lines):
        raise InboundConflictError("已上架数量不可靠取消抹账")
    order.status = STATUS_CANCELLED
    session.commit()
    return _order_to_dict(_get_order(session, order.id))


def putaway(
    session: Session,
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty: Decimal,
    operator_id: int,
    idempotency_key: str,
) -> dict:
    order = _get_order(session, order_id)

    replay = inv.load_increase_idempotent(
        session, idempotency_key=idempotency_key
    )
    if replay is not None:
        return {
            "order": _order_to_dict(order),
            "increase": replay.__dict__,
            "replayed": True,
        }

    if order.status not in PUTAWAY_ALLOWED:
        raise InboundConflictError("当前状态不可上架")

    line = next((ln for ln in order.lines if ln.id == line_id), None)
    if line is None:
        raise InboundNotFoundError("入库单行不存在")

    if qty <= 0:
        raise InboundError("上架数量必须大于 0")
    remaining = line.planned_qty - line.putaway_qty
    if qty > remaining:
        raise InboundError("上架数量超过行剩余计划量")

    location = session.get(Location, location_id)
    if (
        location is None
        or location.status != ActiveStatus.ACTIVE
        or location.warehouse_id != order.warehouse_id
    ):
        raise InboundError("库位不可用或不属于本仓库")

    if is_location_locked(session, location_id):
        raise InboundConflictError("库位已盘点锁定，不可上架")

    # 库存记账成功才算上架成功；失败则整单事务回滚。
    try:
        increase_result = inv.increase(
            session,
            warehouse_id=order.warehouse_id,
            sku_id=line.sku_id,
            location_id=location_id,
            qty=qty,
            ref_type=inv.REF_TYPE_PUTAWAY,
            ref_id=order.id,
            ref_line_id=line.id,
            ref_no=order.order_no,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
    except inv.InventoryError as exc:
        raise InboundConflictError(str(exc)) from exc

    if increase_result.replayed:
        return {
            "order": _order_to_dict(_get_order(session, order.id)),
            "increase": increase_result.__dict__,
            "replayed": True,
        }

    record = PutawayRecord(
        order_id=order.id,
        line_id=line.id,
        location_id=location_id,
        qty=qty,
        operator_id=operator_id,
    )
    session.add(record)
    line.putaway_qty = line.putaway_qty + qty

    if all(ln.putaway_qty >= ln.planned_qty for ln in order.lines):
        order.status = STATUS_DONE
    else:
        order.status = STATUS_PUTAWAY

    session.commit()
    return {
        "order": _order_to_dict(_get_order(session, order.id)),
        "putaway_record_id": record.id,
        "increase": increase_result.__dict__,
        "replayed": False,
    }
