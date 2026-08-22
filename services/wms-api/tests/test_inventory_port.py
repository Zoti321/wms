"""库存记账主缝：increase / allocate / deduct / release / adjust → 余额 + 流水。"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

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


def _increase(
    session,
    *,
    warehouse_id: int,
    sku_id: int,
    location_id: int,
    qty: Decimal,
) -> None:
    inv.increase(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=qty,
        ref_type=inv.REF_TYPE_PUTAWAY,
        ref_id=1,
        ref_line_id=1,
        ref_no="SEED",
        operator_id=1,
        idempotency_key=f"seed-{uuid4().hex}",
    )
    session.commit()


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


def test_allocate_freezes_available_without_changing_on_hand(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("10"),
    )

    result = inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("4"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=50,
        ref_line_id=51,
        ref_no="OUT-ALLOC",
        operator_id=1,
        idempotency_key=f"alloc-{uuid4().hex}",
    )
    db_session.commit()

    assert result.qty_on_hand == "10.000"
    assert result.qty_frozen == "4.000"
    assert result.qty_available == "6.000"
    balances = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert balances["qty_frozen"] == "4.000"
    assert balances["qty_available"] == "6.000"
    ledgers = inv.list_ledgers(db_session, ref_line_id=51)
    assert len(ledgers) == 1
    assert ledgers[0]["ref_type"] == "ALLOCATE"
    assert ledgers[0]["bal_qty"] == "10.000"


def test_allocate_rejects_when_available_insufficient(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("3"),
    )

    with pytest.raises(inv.InventoryInsufficientError):
        inv.allocate(
            db_session,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            qty=Decimal("5"),
            ref_type=inv.REF_TYPE_ALLOCATE,
            ref_id=1,
            ref_line_id=1,
            ref_no="OUT-SHORT",
            operator_id=1,
            idempotency_key=f"short-{uuid4().hex}",
        )
    db_session.rollback()
    balances = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert balances["qty_frozen"] == "0.000"
    assert balances["qty_available"] == "3.000"


def test_deduct_reduces_on_hand_and_frozen(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("10"),
    )
    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("6"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=70,
        ref_line_id=71,
        ref_no="OUT-DED",
        operator_id=1,
        idempotency_key=f"a-{uuid4().hex}",
    )
    db_session.commit()

    result = inv.deduct(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("2"),
        ref_type=inv.REF_TYPE_PICK,
        ref_id=70,
        ref_line_id=71,
        ref_no="OUT-DED",
        operator_id=1,
        idempotency_key=f"d-{uuid4().hex}",
    )
    db_session.commit()

    assert result.qty_on_hand == "8.000"
    assert result.qty_frozen == "4.000"
    assert result.qty_available == "4.000"
    ledgers = inv.list_ledgers(db_session, ref_type="PICK", ref_line_id=71)
    assert len(ledgers) == 1
    assert ledgers[0]["change_qty"] == "-2.000"
    assert ledgers[0]["bal_qty"] == "8.000"


def test_release_returns_frozen_to_available(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("8"),
    )
    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=80,
        ref_line_id=81,
        ref_no="OUT-REL",
        operator_id=1,
        idempotency_key=f"a-{uuid4().hex}",
    )
    db_session.commit()

    result = inv.release(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("3"),
        ref_type=inv.REF_TYPE_RELEASE,
        ref_id=80,
        ref_line_id=81,
        ref_no="OUT-REL",
        operator_id=1,
        idempotency_key=f"r-{uuid4().hex}",
    )
    db_session.commit()

    assert result.qty_on_hand == "8.000"
    assert result.qty_frozen == "2.000"
    assert result.qty_available == "6.000"
    assert inv.list_ledgers(db_session, ref_type="RELEASE", ref_line_id=81)


def test_allocate_idempotent_replay_does_not_double_freeze(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5"),
    )
    key = f"alloc-idem-{uuid4().hex}"
    kwargs = dict(
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("2"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=90,
        ref_line_id=91,
        ref_no="OUT-IDEM",
        operator_id=1,
        idempotency_key=key,
    )
    first = inv.allocate(db_session, **kwargs)
    db_session.commit()
    second = inv.allocate(db_session, **kwargs)
    db_session.commit()

    assert second.replayed is True
    assert second.ledger_id == first.ledger_id
    bal = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert bal["qty_frozen"] == "2.000"


def test_concurrent_allocate_at_most_one_succeeds(db_session) -> None:
    """两笔争用同一可用量：乐观锁下至多一方成功。"""
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5"),
    )

    from app.shared.db import get_session_factory

    factory = get_session_factory()
    s1 = factory()
    s2 = factory()
    try:
        # 两边都读到可用 5，再分别尝试分配 5
        bal1 = inv.list_balances(s1, warehouse_id=warehouse_id)[0]
        bal2 = inv.list_balances(s2, warehouse_id=warehouse_id)[0]
        assert bal1["version"] == bal2["version"] == 1

        ok = 0
        err = 0
        for session, key in ((s1, "c1"), (s2, "c2")):
            try:
                inv.allocate(
                    session,
                    warehouse_id=warehouse_id,
                    sku_id=sku_id,
                    location_id=location_id,
                    qty=Decimal("5"),
                    ref_type=inv.REF_TYPE_ALLOCATE,
                    ref_id=100,
                    ref_line_id=101,
                    ref_no="OUT-RACE",
                    operator_id=1,
                    idempotency_key=key,
                )
                session.commit()
                ok += 1
            except (inv.InventoryConflictError, inv.InventoryInsufficientError):
                session.rollback()
                err += 1
        assert ok == 1
        assert err == 1
        final = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
        assert final["qty_frozen"] == "5.000"
        assert final["qty_available"] == "0.000"
    finally:
        s1.close()
        s2.close()


def test_adjust_gain_increases_on_hand_and_writes_ledger(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("10"),
    )

    result = inv.adjust(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("2.000"),
        ref_type=inv.REF_TYPE_STOCKTAKE,
        ref_id=501,
        ref_line_id=502,
        ref_no="ST-GAIN",
        operator_id=1,
        idempotency_key=f"adj-gain-{uuid4().hex}",
    )
    db_session.commit()

    assert result.qty_on_hand == "12.000"
    assert result.qty_frozen == "0.000"
    assert result.qty_available == "12.000"
    ledgers = inv.list_ledgers(db_session, ref_type="STOCKTAKE", ref_line_id=502)
    assert len(ledgers) == 1
    assert ledgers[0]["change_qty"] == "2.000"
    assert ledgers[0]["bal_qty"] == "12.000"
    assert ledgers[0]["ref_id"] == 501


def test_adjust_loss_decreases_on_hand(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("10"),
    )

    result = inv.adjust(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("-3.000"),
        ref_type=inv.REF_TYPE_STOCKTAKE,
        ref_id=601,
        ref_line_id=602,
        ref_no="ST-LOSS",
        operator_id=1,
        idempotency_key=f"adj-loss-{uuid4().hex}",
    )
    db_session.commit()

    assert result.qty_on_hand == "7.000"
    assert result.qty_available == "7.000"
    ledgers = inv.list_ledgers(db_session, ref_line_id=602)
    assert ledgers[0]["change_qty"] == "-3.000"
    assert ledgers[0]["bal_qty"] == "7.000"


def test_adjust_loss_rejects_when_on_hand_insufficient(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("4"),
    )

    with pytest.raises(inv.InventoryInsufficientError):
        inv.adjust(
            db_session,
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            location_id=location_id,
            qty=Decimal("-5.000"),
            ref_type=inv.REF_TYPE_STOCKTAKE,
            ref_id=1,
            ref_line_id=1,
            ref_no="ST-SHORT",
            operator_id=1,
            idempotency_key=f"adj-short-{uuid4().hex}",
        )
    db_session.rollback()
    bal = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert bal["qty_on_hand"] == "4.000"


def test_adjust_idempotent_replay_does_not_double_book(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("10"),
    )
    key = f"adj-idem-{uuid4().hex}"
    kwargs = dict(
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("1.500"),
        ref_type=inv.REF_TYPE_STOCKTAKE,
        ref_id=701,
        ref_line_id=702,
        ref_no="ST-IDEM",
        operator_id=1,
        idempotency_key=key,
    )
    first = inv.adjust(db_session, **kwargs)
    db_session.commit()
    second = inv.adjust(db_session, **kwargs)
    db_session.commit()

    assert second.replayed is True
    assert second.ledger_id == first.ledger_id
    bal = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
    assert bal["qty_on_hand"] == "11.500"
    assert len(inv.list_ledgers(db_session, ref_line_id=702)) == 1


def test_concurrent_adjust_at_most_one_succeeds(db_session) -> None:
    """两笔争用同一在库：乐观锁下至多一方成功。"""
    warehouse_id, sku_id, location_id = _seed_catalog(db_session)
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5"),
    )

    from app.shared.db import get_session_factory

    factory = get_session_factory()
    s1 = factory()
    s2 = factory()
    try:
        bal1 = inv.list_balances(s1, warehouse_id=warehouse_id)[0]
        bal2 = inv.list_balances(s2, warehouse_id=warehouse_id)[0]
        assert bal1["version"] == bal2["version"] == 1

        ok = 0
        err = 0
        for session, key in ((s1, "adj-c1"), (s2, "adj-c2")):
            try:
                inv.adjust(
                    session,
                    warehouse_id=warehouse_id,
                    sku_id=sku_id,
                    location_id=location_id,
                    qty=Decimal("-5"),
                    ref_type=inv.REF_TYPE_STOCKTAKE,
                    ref_id=800,
                    ref_line_id=801,
                    ref_no="ST-RACE",
                    operator_id=1,
                    idempotency_key=key,
                )
                session.commit()
                ok += 1
            except (inv.InventoryConflictError, inv.InventoryInsufficientError):
                session.rollback()
                err += 1
        assert ok == 1
        assert err == 1
        final = inv.list_balances(db_session, warehouse_id=warehouse_id)[0]
        assert final["qty_on_hand"] == "0.000"
        assert final["version"] == 2
    finally:
        s1.close()
        s2.close()
