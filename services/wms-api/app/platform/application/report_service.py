"""只读经营日报：聚合已有入出库与库存事实，不改账。"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalog.infrastructure.models import Warehouse
from app.inbound.infrastructure.models import InboundOrder, PutawayRecord
from app.inventory.application.inventory_service import ALERT_STATUS_OPEN
from app.inventory.infrastructure.models import InventoryAlert, InventoryBalance
from app.outbound.infrastructure.models import OutboundOrder, PickRecord

CSV_COLUMNS = (
    "warehouse_id",
    "business_date",
    "inbound_order_count",
    "putaway_qty",
    "outbound_order_count",
    "picked_qty",
    "sku_count",
    "total_available",
    "open_alert_count",
)


class ReportError(Exception):
    """报表用例错误基类。"""


class ReportNotFoundError(ReportError):
    """仓库不存在。"""


class ReportValidationError(ReportError):
    """参数非法。"""


def _fmt(qty: Decimal) -> str:
    return f"{qty.quantize(Decimal('0.001'))}"


def _day_bounds(business_date: date) -> tuple[datetime, datetime]:
    """业务日按 UTC 日历日 [00:00, 次日 00:00)。"""
    start = datetime.combine(business_date, time.min)
    end = datetime.combine(
        date.fromordinal(business_date.toordinal() + 1), time.min
    )
    return start, end


def parse_business_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ReportValidationError("business_date 须为 YYYY-MM-DD（UTC）") from exc


def get_daily_report(
    session: Session, *, warehouse_id: int, business_date: date
) -> dict:
    if session.get(Warehouse, warehouse_id) is None:
        raise ReportNotFoundError("仓库不存在")

    start, end = _day_bounds(business_date)

    inbound_order_count = session.scalar(
        select(func.count(func.distinct(PutawayRecord.order_id)))
        .select_from(PutawayRecord)
        .join(InboundOrder, InboundOrder.id == PutawayRecord.order_id)
        .where(
            InboundOrder.warehouse_id == warehouse_id,
            PutawayRecord.created_at >= start,
            PutawayRecord.created_at < end,
        )
    ) or 0

    putaway_qty = session.scalar(
        select(func.coalesce(func.sum(PutawayRecord.qty), 0))
        .select_from(PutawayRecord)
        .join(InboundOrder, InboundOrder.id == PutawayRecord.order_id)
        .where(
            InboundOrder.warehouse_id == warehouse_id,
            PutawayRecord.created_at >= start,
            PutawayRecord.created_at < end,
        )
    )
    putaway_qty = Decimal(putaway_qty or 0)

    outbound_order_count = session.scalar(
        select(func.count(func.distinct(PickRecord.order_id)))
        .select_from(PickRecord)
        .join(OutboundOrder, OutboundOrder.id == PickRecord.order_id)
        .where(
            OutboundOrder.warehouse_id == warehouse_id,
            PickRecord.created_at >= start,
            PickRecord.created_at < end,
        )
    ) or 0

    picked_qty = session.scalar(
        select(func.coalesce(func.sum(PickRecord.qty), 0))
        .select_from(PickRecord)
        .join(OutboundOrder, OutboundOrder.id == PickRecord.order_id)
        .where(
            OutboundOrder.warehouse_id == warehouse_id,
            PickRecord.created_at >= start,
            PickRecord.created_at < end,
        )
    )
    picked_qty = Decimal(picked_qty or 0)

    sku_count = session.scalar(
        select(func.count(func.distinct(InventoryBalance.sku_id))).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.qty_on_hand > 0,
        )
    ) or 0

    total_available = session.scalar(
        select(
            func.coalesce(
                func.sum(
                    InventoryBalance.qty_on_hand - InventoryBalance.qty_frozen
                ),
                0,
            )
        ).where(InventoryBalance.warehouse_id == warehouse_id)
    )
    total_available = Decimal(total_available or 0)

    open_alert_count = session.scalar(
        select(func.count()).select_from(InventoryAlert).where(
            InventoryAlert.warehouse_id == warehouse_id,
            InventoryAlert.status == ALERT_STATUS_OPEN,
        )
    ) or 0

    return {
        "warehouse_id": warehouse_id,
        "business_date": business_date.isoformat(),
        "inbound_order_count": int(inbound_order_count),
        "putaway_qty": _fmt(putaway_qty),
        "outbound_order_count": int(outbound_order_count),
        "picked_qty": _fmt(picked_qty),
        "sku_count": int(sku_count),
        "total_available": _fmt(total_available),
        "open_alert_count": int(open_alert_count),
    }


def daily_report_to_csv(report: dict) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerow({col: report[col] for col in CSV_COLUMNS})
    return buf.getvalue()
