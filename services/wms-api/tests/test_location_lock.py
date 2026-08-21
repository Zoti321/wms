"""盘点锁主缝：独立锁数据 + is_location_locked；与冻结数量无关。"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.catalog.infrastructure.models import Location, Sku, Warehouse
from app.inventory.application import inventory_service as inv
from app.inventory.application import lock as lock_port


def _seed(session) -> tuple[int, int, int, int]:
    wh = Warehouse(warehouse_code="WH-LOCK", name="锁测试仓", status=1)
    sku = Sku(sku_code="SKU-LOCK", name="锁SKU", unit="PCS", safety_stock=Decimal("0"))
    session.add_all([wh, sku])
    session.flush()
    loc_a = Location(
        warehouse_id=wh.id,
        location_code="L-A",
        zone="A",
        aisle="01",
        bin="01",
        space_status=1,
        status=1,
    )
    loc_b = Location(
        warehouse_id=wh.id,
        location_code="L-B",
        zone="B",
        aisle="01",
        bin="02",
        space_status=1,
        status=1,
    )
    session.add_all([loc_a, loc_b])
    session.commit()
    return wh.id, sku.id, loc_a.id, loc_b.id


def test_acquire_makes_location_locked_and_release_clears(db_session) -> None:
    _, _, loc_a, loc_b = _seed(db_session)
    assert lock_port.is_location_locked(db_session, loc_a) is False

    lock_port.acquire_location_locks(
        db_session,
        location_ids=[loc_a],
        ref_type="STOCKTAKE",
        ref_id=11,
    )
    db_session.commit()

    assert lock_port.is_location_locked(db_session, loc_a) is True
    assert lock_port.is_location_locked(db_session, loc_b) is False

    lock_port.release_location_locks(
        db_session, ref_type="STOCKTAKE", ref_id=11
    )
    db_session.commit()
    assert lock_port.is_location_locked(db_session, loc_a) is False


def test_acquire_rejects_duplicate_lock_on_same_location(db_session) -> None:
    _, _, loc_a, _ = _seed(db_session)
    lock_port.acquire_location_locks(
        db_session,
        location_ids=[loc_a],
        ref_type="STOCKTAKE",
        ref_id=1,
    )
    db_session.commit()

    with pytest.raises(lock_port.LocationLockConflictError):
        lock_port.acquire_location_locks(
            db_session,
            location_ids=[loc_a],
            ref_type="STOCKTAKE",
            ref_id=2,
        )
    db_session.rollback()


def test_lock_does_not_change_inventory_frozen_qty(db_session) -> None:
    warehouse_id, sku_id, loc_a, _ = _seed(db_session)
    inv.increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=loc_a,
        qty=Decimal("5"),
        ref_type=inv.REF_TYPE_PUTAWAY,
        ref_id=1,
        ref_line_id=1,
        ref_no="SEED",
        operator_id=1,
        idempotency_key=f"seed-{uuid4().hex}",
    )
    db_session.commit()

    lock_port.acquire_location_locks(
        db_session,
        location_ids=[loc_a],
        ref_type="STOCKTAKE",
        ref_id=99,
    )
    db_session.commit()

    bal = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert bal["qty_on_hand"] == "5.000"
    assert bal["qty_frozen"] == "0.000"
    assert bal["qty_available"] == "5.000"
