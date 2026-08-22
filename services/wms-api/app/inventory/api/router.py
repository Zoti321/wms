"""库存查询 HTTP。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.inventory.application import inventory_service as svc
from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.domain.permissions import PERM_INVENTORY_READ
from app.shared.db import get_db
from app.shared.response import ok

router = APIRouter(tags=["inventory"])


@router.get("/inventories/alerts")
def list_inventory_alerts(
    warehouse_id: int | None = None,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INVENTORY_READ)),
) -> dict:
    items = svc.list_alerts(session, warehouse_id=warehouse_id)
    return ok({"items": items})


@router.get("/inventories")
def list_inventories(
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    location_id: int | None = None,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INVENTORY_READ)),
) -> dict:
    items = svc.list_balances(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
    )
    return ok({"items": items})


@router.get("/inventories/ledgers")
def list_inventory_ledgers(
    warehouse_id: int | None = None,
    sku_id: int | None = None,
    ref_line_id: int | None = None,
    ref_id: int | None = None,
    ref_type: str | None = None,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INVENTORY_READ)),
) -> dict:
    items = svc.list_ledgers(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        ref_line_id=ref_line_id,
        ref_id=ref_id,
        ref_type=ref_type,
    )
    return ok({"items": items})
