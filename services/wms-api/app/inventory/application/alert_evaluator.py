"""记账后同步预警判定（ADR-0001：无 Redis，随记账成功执行）。"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.catalog.infrastructure.models import Sku
from app.inventory.application.types import ALERT_STATUS_CLEARED, ALERT_STATUS_OPEN, fmt_qty
from app.inventory.infrastructure.models import InventoryAlert, InventoryBalance
from app.shared.pagination import paginate, paginated_payload


def _sum_available(
    session: Session, *, warehouse_id: int, sku_id: int
) -> Decimal:
    row = session.execute(
        select(
            func.coalesce(
                func.sum(InventoryBalance.qty_on_hand - InventoryBalance.qty_frozen),
                0,
            )
        ).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.sku_id == sku_id,
        )
    ).scalar_one()
    return Decimal(row)


def evaluate(session: Session, *, warehouse_id: int, sku_id: int) -> None:
    """汇总可用 < 安全库存则打开预警，否则解除。阈值为 0 不预警。"""
    sku = session.get(Sku, sku_id)
    if sku is None:
        return
    threshold = sku.safety_stock
    available = _sum_available(session, warehouse_id=warehouse_id, sku_id=sku_id)
    alert = session.scalars(
        select(InventoryAlert).where(
            InventoryAlert.warehouse_id == warehouse_id,
            InventoryAlert.sku_id == sku_id,
        )
    ).first()

    should_open = threshold > 0 and available < threshold
    now = datetime.now(UTC).replace(tzinfo=None)

    if should_open:
        # upsert：避免并发双插唯一键冲突把已成功记账一并回滚
        stmt = mysql_insert(InventoryAlert).values(
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            qty_available=available,
            safety_stock=threshold,
            status=ALERT_STATUS_OPEN,
            created_at=now,
            cleared_at=None,
        )
        stmt = stmt.on_duplicate_key_update(
            qty_available=stmt.inserted.qty_available,
            safety_stock=stmt.inserted.safety_stock,
            status=ALERT_STATUS_OPEN,
            cleared_at=None,
            created_at=func.if_(
                InventoryAlert.status == ALERT_STATUS_CLEARED,
                stmt.inserted.created_at,
                InventoryAlert.created_at,
            ),
        )
        session.execute(stmt)
        if alert is not None:
            session.expire(alert)
        return

    if alert is not None and alert.status == ALERT_STATUS_OPEN:
        alert.qty_available = available
        alert.safety_stock = threshold
        alert.status = ALERT_STATUS_CLEARED
        alert.cleared_at = now


def list_alerts(
    session: Session,
    *,
    warehouse_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """只读有效（open）预警；可按仓库筛选。"""
    stmt = select(InventoryAlert).where(InventoryAlert.status == ALERT_STATUS_OPEN)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryAlert.warehouse_id == warehouse_id)
    stmt = stmt.order_by(InventoryAlert.created_at.desc(), InventoryAlert.id.desc())
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [
            {
                "id": row.id,
                "warehouse_id": row.warehouse_id,
                "sku_id": row.sku_id,
                "qty_available": fmt_qty(row.qty_available),
                "safety_stock": fmt_qty(row.safety_stock),
                "status": row.status,
                "created_at": row.created_at.isoformat(sep=" ", timespec="seconds"),
            }
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
