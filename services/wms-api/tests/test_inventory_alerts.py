"""库存预警：记账成功后同步判定；GET /inventories/alerts 只读有效预警。"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.catalog.infrastructure.models import Location, Sku, Warehouse
from app.inventory.application import inventory_service as inv


def _seed(
    session,
    *,
    safety_stock: Decimal,
    sku_code: str = "SKU-ALERT",
    warehouse_code: str = "WH-ALERT",
) -> tuple[int, int, int]:
    wh = Warehouse(warehouse_code=warehouse_code, name="预警仓", status=1)
    sku = Sku(
        sku_code=sku_code,
        name="预警SKU",
        unit="PCS",
        safety_stock=safety_stock,
    )
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


def _open_alert_via_allocate(
    session,
    *,
    warehouse_id: int,
    sku_id: int,
    location_id: int,
    on_hand: Decimal,
    allocate_qty: Decimal,
) -> None:
    _increase(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=on_hand,
    )
    inv.allocate(
        session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=allocate_qty,
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=50,
        ref_line_id=51,
        ref_no="OUT-ALERT",
        operator_id=1,
        idempotency_key=f"alloc-{uuid4().hex}",
    )
    session.commit()


def test_allocate_below_safety_stock_opens_alert(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("12"),
    )

    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []

    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("3"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=50,
        ref_line_id=51,
        ref_no="OUT-ALERT",
        operator_id=1,
        idempotency_key=f"alloc-{uuid4().hex}",
    )
    db_session.commit()

    alerts = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']
    assert len(alerts) == 1
    assert alerts[0]["warehouse_id"] == warehouse_id
    assert alerts[0]["sku_id"] == sku_id
    assert alerts[0]["qty_available"] == "9.000"
    assert alerts[0]["safety_stock"] == "10.000"
    assert alerts[0]["status"] == "open"


def test_release_restores_available_and_clears_alert(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )
    assert len(inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']) == 1

    inv.release(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("3"),
        ref_type=inv.REF_TYPE_RELEASE,
        ref_id=50,
        ref_line_id=51,
        ref_no="OUT-ALERT",
        operator_id=1,
        idempotency_key=f"rel-{uuid4().hex}",
    )
    db_session.commit()

    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []


def test_increase_clears_alert_when_available_recovers(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )

    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("5"),
    )
    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []


def test_adjust_loss_opens_alert_and_gain_clears(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("12"),
    )

    inv.adjust(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("-3"),
        ref_type=inv.REF_TYPE_STOCKTAKE,
        ref_id=90,
        ref_line_id=91,
        ref_no="ST-ALERT",
        operator_id=1,
        idempotency_key=f"adj-loss-{uuid4().hex}",
    )
    db_session.commit()
    alerts = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']
    assert len(alerts) == 1
    assert alerts[0]["qty_available"] == "9.000"

    inv.adjust(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("2"),
        ref_type=inv.REF_TYPE_STOCKTAKE,
        ref_id=90,
        ref_line_id=92,
        ref_no="ST-ALERT",
        operator_id=1,
        idempotency_key=f"adj-gain-{uuid4().hex}",
    )
    db_session.commit()
    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []


def test_zero_safety_stock_never_opens_alert(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("0")
    )
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("1"),
    )
    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("1"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=1,
        ref_line_id=1,
        ref_no="OUT-ZERO",
        operator_id=1,
        idempotency_key=f"alloc-{uuid4().hex}",
    )
    db_session.commit()
    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []


def test_repeated_allocate_keeps_single_open_alert(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )
    first_id = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'][0]["id"]

    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("1"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=51,
        ref_line_id=52,
        ref_no="OUT-ALERT2",
        operator_id=1,
        idempotency_key=f"alloc2-{uuid4().hex}",
    )
    db_session.commit()

    alerts = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']
    assert len(alerts) == 1
    assert alerts[0]["id"] == first_id
    assert alerts[0]["qty_available"] == "8.000"


def test_list_alerts_filters_by_warehouse(db_session) -> None:
    wh1, sku1, loc1 = _seed(
        db_session,
        safety_stock=Decimal("10"),
        sku_code="SKU-A1",
        warehouse_code="WH-A1",
    )
    wh2, sku2, loc2 = _seed(
        db_session,
        safety_stock=Decimal("10"),
        sku_code="SKU-A2",
        warehouse_code="WH-A2",
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=wh1,
        sku_id=sku1,
        location_id=loc1,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=wh2,
        sku_id=sku2,
        location_id=loc2,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )

    only_wh1 = inv.list_alerts(db_session, warehouse_id=wh1)['items']
    assert len(only_wh1) == 1
    assert only_wh1[0]["warehouse_id"] == wh1
    assert len(inv.list_alerts(db_session)['items']) == 2


def test_get_alerts_requires_bearer_and_returns_open(
    client: TestClient, auth_headers: dict[str, str], db_session
) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )

    anon = client.get("/api/v1/inventories/alerts")
    assert anon.status_code == 401

    resp = client.get(
        "/api/v1/inventories/alerts",
        headers=auth_headers,
        params={"warehouse_id": warehouse_id},
    )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["sku_id"] == sku_id
    assert items[0]["status"] == "open"


def test_alert_uses_cross_location_available_sum(db_session) -> None:
    warehouse_id, sku_id, loc1 = _seed(db_session, safety_stock=Decimal("10"))
    loc2 = Location(
        warehouse_id=warehouse_id,
        location_code="A-01-02",
        zone="A",
        aisle="01",
        bin="02",
        space_status=1,
        status=1,
    )
    db_session.add(loc2)
    db_session.commit()

    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=loc1,
        qty=Decimal("6"),
    )
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=loc2.id,
        qty=Decimal("5"),
    )
    # 跨库位合计 11 >= 10，无预警
    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []

    inv.allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=loc1,
        qty=Decimal("2"),
        ref_type=inv.REF_TYPE_ALLOCATE,
        ref_id=1,
        ref_line_id=1,
        ref_no="OUT-CROSS",
        operator_id=1,
        idempotency_key=f"cross-{uuid4().hex}",
    )
    db_session.commit()
    # 合计可用 9 < 10
    alerts = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']
    assert len(alerts) == 1
    assert alerts[0]["qty_available"] == "9.000"


def test_available_equal_to_safety_stock_clears_alert(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )
    # 可用 9；再上架 1 → 可用 10，等于阈值应解除
    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("1"),
    )
    assert inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'] == []


def test_increase_still_below_threshold_keeps_alert_open(db_session) -> None:
    warehouse_id, sku_id, location_id = _seed(
        db_session, safety_stock=Decimal("10")
    )
    _open_alert_via_allocate(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        on_hand=Decimal("12"),
        allocate_qty=Decimal("3"),
    )
    first_id = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items'][0]["id"]

    _increase(
        db_session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        location_id=location_id,
        qty=Decimal("0.5"),
    )
    alerts = inv.list_alerts(db_session, warehouse_id=warehouse_id)['items']
    assert len(alerts) == 1
    assert alerts[0]["id"] == first_id
    assert alerts[0]["qty_available"] == "9.500"
