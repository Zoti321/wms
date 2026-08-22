"""盘点 HTTP 次缝：加锁 → 进出拒绝 → 实盘 → 审核调账 → 流水 → 释锁；取消/幂等。"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.inventory.application.lock import is_location_locked
from app.shared.db import get_session_factory
from tests.http_scenarios import putaway_stock, seed_masters


def test_stocktake_write_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/stocktakes",
        json={"warehouse_id": 1},
        headers={"Idempotency-Key": "anon"},
    )
    assert response.status_code == 401


def test_stocktake_full_cycle_lock_count_approve_unlock(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="ST", extra_location=True)
    putaway_stock(client, auth_headers, masters, qty_planned="10.000")

    # 盘前先分配，盘中拣货应被拒
    outbound = client.post(
        "/api/v1/outbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "sales",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
        },
    )
    assert outbound.status_code == 200
    out_id = outbound.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/outbound-orders/{out_id}/submit", headers=auth_headers
        ).status_code
        == 200
    )
    out_line_id = client.get(
        f"/api/v1/outbound-orders/{out_id}", headers=auth_headers
    ).json()["data"]["lines"][0]["id"]
    assert (
        client.post(
            f"/api/v1/outbound-orders/{out_id}/approve",
            headers={**auth_headers, "Idempotency-Key": f"st-oa-pre-{uuid4().hex}"},
            json={
                "allocations": [
                    {"line_id": out_line_id, "location_id": masters["location_id"]}
                ]
            },
        ).status_code
        == 200
    )

    created = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": f"st-c-{uuid4().hex}"},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    assert created.status_code == 200, created.text
    payload = created.json()["data"]
    order = payload["order"]
    assert order["status"] == "counting"
    assert len(order["lines"]) == 1
    assert order["lines"][0]["book_qty"] == "10.000"
    assert order["lines"][0]["counted_qty"] is None
    line_id = order["lines"][0]["id"]
    order_id = order["id"]

    session = get_session_factory()()
    try:
        assert is_location_locked(session, masters["location_id"]) is True
        assert is_location_locked(session, masters["location_b_id"]) is False
    finally:
        session.close()

    # 盘中：上架被拒
    inbound = client.post(
        "/api/v1/inbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
        },
    )
    assert inbound.status_code == 200
    inb_id = inbound.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/inbound-orders/{inb_id}/submit", headers=auth_headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/inbound-orders/{inb_id}/approve", headers=auth_headers
        ).status_code
        == 200
    )
    inb_line_id = client.get(
        f"/api/v1/inbound-orders/{inb_id}", headers=auth_headers
    ).json()["data"]["lines"][0]["id"]
    putaway = client.post(
        f"/api/v1/inbound-orders/{inb_id}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"st-pw-{uuid4().hex}"},
        json={
            "line_id": inb_line_id,
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    assert putaway.status_code == 409, putaway.text

    # 盘中：拣货被拒
    pick = client.post(
        f"/api/v1/outbound-orders/{out_id}/pick",
        headers={**auth_headers, "Idempotency-Key": f"st-pk-{uuid4().hex}"},
        json={
            "line_id": out_line_id,
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    assert pick.status_code == 409, pick.text

    # 实盘录入：审核前余额不变
    counts = client.post(
        f"/api/v1/stocktakes/{order_id}/counts",
        headers=auth_headers,
        json={"lines": [{"line_id": line_id, "counted_qty": "12.000"}]},
    )
    assert counts.status_code == 200, counts.text
    assert counts.json()["data"]["lines"][0]["diff_qty"] == "2.000"

    bal_before = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={
            "warehouse_id": masters["warehouse_id"],
            "sku_id": masters["sku_id"],
        },
    ).json()["data"]["items"][0]
    assert bal_before["qty_on_hand"] == "10.000"

    approved = client.post(
        f"/api/v1/stocktakes/{order_id}/approve",
        headers={**auth_headers, "Idempotency-Key": f"st-ap-{uuid4().hex}"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["order"]["status"] == "approved"

    bal_after = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={
            "warehouse_id": masters["warehouse_id"],
            "sku_id": masters["sku_id"],
        },
    ).json()["data"]["items"][0]
    assert bal_after["qty_on_hand"] == "12.000"

    ledgers = client.get(
        "/api/v1/inventories/ledgers",
        headers=auth_headers,
        params={"ref_type": "STOCKTAKE", "ref_id": order_id},
    )
    assert ledgers.status_code == 200
    items = ledgers.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["change_qty"] == "2.000"
    assert items[0]["ref_line_id"] == line_id

    session = get_session_factory()()
    try:
        assert is_location_locked(session, masters["location_id"]) is False
    finally:
        session.close()

    # 释锁后可再上架
    putaway_ok = client.post(
        f"/api/v1/inbound-orders/{inb_id}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"st-pw3-{uuid4().hex}"},
        json={
            "line_id": inb_line_id,
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    assert putaway_ok.status_code == 200, putaway_ok.text

    # 已完成不可再编辑
    again = client.post(
        f"/api/v1/stocktakes/{order_id}/counts",
        headers=auth_headers,
        json={"lines": [{"line_id": line_id, "counted_qty": "1.000"}]},
    )
    assert again.status_code == 409


def test_stocktake_cancel_releases_lock(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="ST", extra_location=True)
    putaway_stock(client, auth_headers, masters)

    created = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": f"st-cc-{uuid4().hex}"},
        json={"warehouse_id": masters["warehouse_id"]},
    )
    assert created.status_code == 200
    order_id = created.json()["data"]["order"]["id"]

    cancelled = client.post(
        f"/api/v1/stocktakes/{order_id}/cancel",
        headers={**auth_headers, "Idempotency-Key": f"st-cx-{uuid4().hex}"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["order"]["status"] == "cancelled"

    session = get_session_factory()()
    try:
        assert is_location_locked(session, masters["location_id"]) is False
    finally:
        session.close()


def test_stocktake_create_idempotent(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="ST", extra_location=True)
    putaway_stock(client, auth_headers, masters)
    key = f"st-create-idem-{uuid4().hex}"
    first = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": key},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": key},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    assert second.status_code == 200
    assert second.json()["data"]["replayed"] is True
    assert second.json()["data"]["order"]["id"] == first.json()["data"]["order"]["id"]


def test_stocktake_approve_forbidden_for_non_supervisor(db_session) -> None:
    from decimal import Decimal

    from app.catalog.infrastructure.models import Location, Sku, Warehouse
    from app.inventory.application import inventory_service as inv
    from app.stocktake.application import stocktake_service as st

    wh = Warehouse(warehouse_code="WH-ROLE", name="角色仓", status=1)
    sku = Sku(sku_code="SKU-ROLE", name="角色SKU", unit="PCS", safety_stock=Decimal("0"))
    db_session.add_all([wh, sku])
    db_session.flush()
    loc = Location(
        warehouse_id=wh.id,
        location_code="R-01",
        zone="A",
        aisle="01",
        bin="01",
        space_status=1,
        status=1,
    )
    db_session.add(loc)
    db_session.commit()
    inv.increase(
        db_session,
        warehouse_id=wh.id,
        sku_id=sku.id,
        location_id=loc.id,
        qty=Decimal("2"),
        ref_type=inv.REF_TYPE_PUTAWAY,
        ref_id=1,
        ref_line_id=1,
        ref_no="SEED",
        operator_id=1,
        idempotency_key=f"seed-{uuid4().hex}",
    )
    db_session.commit()
    created = st.create_order(
        db_session,
        warehouse_id=wh.id,
        zone="A",
        created_by=1,
        idempotency_key=f"role-c-{uuid4().hex}",
    )
    order_id = created["order"]["id"]
    line_id = created["order"]["lines"][0]["id"]
    st.record_counts(
        db_session,
        order_id,
        lines=[{"line_id": line_id, "counted_qty": Decimal("2")}],
    )
    with pytest.raises(st.StocktakeForbiddenError):
        st.approve_order(
            db_session,
            order_id,
            operator_id=2,
            role_code="warehouse_worker",
            idempotency_key=f"role-a-{uuid4().hex}",
        )


def test_stocktake_approve_idempotent(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="ST", extra_location=True)
    putaway_stock(client, auth_headers, masters, qty_planned="5.000")
    created = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": f"st-ic-{uuid4().hex}"},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    order = created.json()["data"]["order"]
    line_id = order["lines"][0]["id"]
    client.post(
        f"/api/v1/stocktakes/{order['id']}/counts",
        headers=auth_headers,
        json={"lines": [{"line_id": line_id, "counted_qty": "4.000"}]},
    )
    key = f"st-iap-{uuid4().hex}"
    first = client.post(
        f"/api/v1/stocktakes/{order['id']}/approve",
        headers={**auth_headers, "Idempotency-Key": key},
    )
    assert first.status_code == 200
    second = client.post(
        f"/api/v1/stocktakes/{order['id']}/approve",
        headers={**auth_headers, "Idempotency-Key": key},
    )
    assert second.status_code == 200
    assert second.json()["data"]["replayed"] is True
    bal = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"][0]
    assert bal["qty_on_hand"] == "4.000"
    ledgers = client.get(
        "/api/v1/inventories/ledgers",
        headers=auth_headers,
        params={"ref_type": "STOCKTAKE", "ref_id": order["id"]},
    ).json()["data"]["items"]
    assert len(ledgers) == 1


def test_stocktake_approve_loss_insufficient_keeps_lock(client, auth_headers) -> None:
    """盘亏超出在库：整单失败、不落账、不释锁。"""
    masters = seed_masters(client, auth_headers, prefix="ST", extra_location=True)
    putaway_stock(client, auth_headers, masters, qty_planned="3.000")

    # 先分配冻结 2，使在库 3 但盘亏到 0 仍 >= frozen；要失败需盘亏超过 on_hand。
    # 直接 counted=0 对 on_hand=3 是合法盘亏。改为：账面 3，录入后通过端口外手段不够——
    # 用 counted 合法但我们模拟「账面被并发改掉」较难。改为盘点行 book=3 counted=- 不允许。
    # 验收：盘亏使 on_hand 低于 frozen 时失败——先出库分配冻结。
    outbound = client.post(
        "/api/v1/outbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "sales",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "2.000"}],
        },
    )
    out_id = outbound.json()["data"]["id"]
    client.post(f"/api/v1/outbound-orders/{out_id}/submit", headers=auth_headers)
    out_line = client.get(
        f"/api/v1/outbound-orders/{out_id}", headers=auth_headers
    ).json()["data"]["lines"][0]["id"]
    # 分配必须在盘点锁之前
    assert (
        client.post(
            f"/api/v1/outbound-orders/{out_id}/approve",
            headers={**auth_headers, "Idempotency-Key": f"pre-{uuid4().hex}"},
            json={
                "allocations": [
                    {"line_id": out_line, "location_id": masters["location_id"]}
                ]
            },
        ).status_code
        == 200
    )

    created = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": f"st-short-c-{uuid4().hex}"},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    assert created.status_code == 200, created.text
    order = created.json()["data"]["order"]
    # book_qty 快照为加锁时在库 3；实盘 0 → delta -3，但 frozen=2 → on_hand 不能到 0
    client.post(
        f"/api/v1/stocktakes/{order['id']}/counts",
        headers=auth_headers,
        json={
            "lines": [
                {"line_id": order["lines"][0]["id"], "counted_qty": "0.000"}
            ]
        },
    )
    failed = client.post(
        f"/api/v1/stocktakes/{order['id']}/approve",
        headers={**auth_headers, "Idempotency-Key": f"st-short-a-{uuid4().hex}"},
    )
    assert failed.status_code == 400, failed.text

    bal = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"][0]
    assert bal["qty_on_hand"] == "3.000"
    assert bal["qty_frozen"] == "2.000"

    session = get_session_factory()()
    try:
        assert is_location_locked(session, masters["location_id"]) is True
    finally:
        session.close()

    detail = client.get(f"/api/v1/stocktakes/{order['id']}", headers=auth_headers)
    assert detail.json()["data"]["status"] == "counting"
