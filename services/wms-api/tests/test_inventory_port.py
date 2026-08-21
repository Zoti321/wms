"""库存记账主缝：increase → 余额 + 流水。"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.catalog.infrastructure.models import Location, Sku, Warehouse
from app.inventory.application import inventory_service as inv


def _seed_catalog(session) -> tuple[int, int, int]:
    wh = Warehouse(warehouse_code="WH-INV", name="库存仓", status=1)
    sku = Sku(sku_code="SKU-INV", name="测试SKU", unit="PCS", safety_stock=Decimal("0"))
    session.add_all([wh, sku])
    session.flush()
    loc = Location(
        warehouse_id=wh.id,
        location_code="A-01-01",
        zone="A",
        aisle="01",
        bin="01",
        space_status=1,
        status=1,
    )
    session.add(loc)
    session.commit()
    return wh.id, sku.id, loc.id


def test_increase_updates_balance_and_writes_ledger(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    key = f"inc-{uuid4().hex}"

    result = inv.increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5.000"),
        ref_type=inv.REF_TYPE_PUTAWAY,
        ref_id=100,
        ref_line_id=200,
        ref_no="INB-TEST",
        operator_id=1,
        idempotency_key=key,
    )
    db_session.commit()

    assert result.qty_on_hand == "5.000"
    assert result.qty_frozen == "0.000"
    assert result.qty_available == "5.000"
    assert result.replayed is False

    balances = inv.list_balances(db_session, warehouse_id=warehouse_id, sku_id=sku_id)
    assert len(balances) == 1
    assert balances[0]["qty_on_hand"] == "5.000"
    assert balances[0]["qty_available"] == "5.000"

    ledgers = inv.list_ledgers(db_session, ref_line_id=200)
    assert len(ledgers) == 1
    assert ledgers[0]["change_qty"] == "5.000"
    assert ledgers[0]["bal_qty"] == "5.000"
    assert ledgers[0]["ref_type"] == "PUTAWAY"


def test_increase_idempotent_replay_does_not_double_book(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    key = f"inc-{uuid4().hex}"
    kwargs = dict(
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("3.000"),
        ref_type=inv.REF_TYPE_PUTAWAY,
        ref_id=1,
        ref_line_id=2,
        ref_no="INB-IDEMP",
        operator_id=1,
        idempotency_key=key,
    )
    first = inv.increase(db_session, **kwargs)
    db_session.commit()
    second = inv.increase(db_session, **kwargs)
    db_session.commit()

    assert second.replayed is True
    assert second.ledger_id == first.ledger_id
    balances = inv.list_balances(db_session, warehouse_id=warehouse_id)
    assert balances[0]["qty_on_hand"] == "3.000"
    assert len(inv.list_ledgers(db_session, ref_id=1)) == 1


def test_partial_increase_accumulates_balance_and_multiple_ledgers(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    for i, qty in enumerate((Decimal("2"), Decimal("3")), start=1):
        inv.increase(
            db_session,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            qty=qty,
            ref_type=inv.REF_TYPE_PUTAWAY,
            ref_id=10,
            ref_line_id=20,
            ref_no="INB-PART",
            operator_id=1,
            idempotency_key=f"part-{i}-{uuid4().hex}",
        )
        db_session.commit()

    balances = inv.list_balances(db_session, warehouse_id=warehouse_id)
    assert balances[0]["qty_on_hand"] == "5.000"
    ledgers = inv.list_ledgers(db_session, ref_line_id=20)
    assert len(ledgers) == 2
