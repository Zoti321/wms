"""出库 HTTP 次缝：建单 → 审核分配 → 部分拣货 → 取消未拣；不足整单失败；锁/幂等。"""

from __future__ import annotations

from uuid import uuid4

from app.inventory.application.lock import set_location_lock_checker
from tests.http_scenarios import (
    approve_outbound,
    idem_headers,
    list_balances,
    list_ledgers,
    pending_outbound,
    pick_outbound,
    putaway_stock,
    seed_masters,
)


def test_outbound_write_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/outbound-orders",
        json={
            "warehouse_id": 1,
            "order_type": "sales",
            "lines": [{"sku_id": 1, "planned_qty": "1"}],
        },
    )
    assert response.status_code == 401


def test_inbound_to_outbound_main_path(client, auth_headers) -> None:
    """入库上架 → 审核分配 → 部分拣货 → 取消未拣 → 流水核对。"""
    masters = seed_masters(
        client, auth_headers, prefix="OUT", location_code="B-01-01", zone="B"
    )
    putaway_stock(client, auth_headers, masters, "10.000")

    pending = pending_outbound(client, auth_headers, masters, "10.000")
    approved = approve_outbound(client, auth_headers, pending, masters["location_id"])
    assert approved.status_code == 200, approved.text
    order = approved.json()["data"]["order"]
    assert order["status"] == "approved"
    assert order["lines"][0]["allocated_qty"] == "10.000"

    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_on_hand"] == "10.000"
    assert items[0]["qty_frozen"] == "10.000"
    assert items[0]["qty_available"] == "0.000"

    line_id = order["lines"][0]["id"]
    pick1 = pick_outbound(
        client,
        auth_headers,
        order["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_pick="4.000",
        idempotency_key=f"pk1-{uuid4().hex}",
    )
    assert pick1.status_code == 200, pick1.text
    assert pick1.json()["data"]["order"]["status"] == "picking"
    assert pick1.json()["data"]["order"]["lines"][0]["picked_qty"] == "4.000"

    cancelled = client.post(
        f"/api/v1/outbound-orders/{order['id']}/cancel",
        headers=idem_headers(auth_headers, f"cx-{uuid4().hex}"),
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["order"]["status"] == "done"
    assert "退货入库" in (cancelled.json()["data"].get("note") or "")
    assert cancelled.json()["data"]["order"]["lines"][0]["picked_qty"] == "4.000"
    assert cancelled.json()["data"]["order"]["lines"][0]["allocated_qty"] == "4.000"

    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_on_hand"] == "6.000"
    assert items[0]["qty_frozen"] == "0.000"
    assert items[0]["qty_available"] == "6.000"

    types = [row["ref_type"] for row in list_ledgers(client, auth_headers, ref_line_id=line_id)]
    assert "ALLOCATE" in types
    assert "PICK" in types
    assert "RELEASE" in types


def test_approve_insufficient_fails_without_reservation(client, auth_headers) -> None:
    masters = seed_masters(
        client, auth_headers, prefix="OUT", location_code="B-01-01", zone="B"
    )
    putaway_stock(client, auth_headers, masters, "3.000")
    pending = pending_outbound(client, auth_headers, masters, "5.000")

    response = approve_outbound(client, auth_headers, pending, masters["location_id"])
    assert response.status_code == 400

    detail = client.get(
        f"/api/v1/outbound-orders/{pending['id']}", headers=auth_headers
    ).json()["data"]
    assert detail["status"] == "pending"
    assert detail["lines"][0]["allocated_qty"] == "0.000"

    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_frozen"] == "0.000"
    assert items[0]["qty_available"] == "3.000"


def test_approve_and_pick_idempotent(client, auth_headers) -> None:
    masters = seed_masters(
        client, auth_headers, prefix="OUT", location_code="B-01-01", zone="B"
    )
    putaway_stock(client, auth_headers, masters, "5.000")
    pending = pending_outbound(client, auth_headers, masters, "5.000")
    key = f"idem-ap-{uuid4().hex}"

    r1 = approve_outbound(
        client, auth_headers, pending, masters["location_id"], key=key
    )
    r2 = approve_outbound(
        client, auth_headers, pending, masters["location_id"], key=key
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["data"]["replayed"] is True

    order = r1.json()["data"]["order"]
    pick_key = f"idem-pk-{uuid4().hex}"
    payload = {
        "line_id": order["lines"][0]["id"],
        "location_id": masters["location_id"],
        "qty": "5.000",
    }
    p1 = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers=idem_headers(auth_headers, pick_key),
        json=payload,
    )
    p2 = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers=idem_headers(auth_headers, pick_key),
        json=payload,
    )
    assert p1.status_code == 200
    assert p2.status_code == 200
    assert p2.json()["data"]["replayed"] is True
    assert p1.json()["data"]["order"]["status"] == "done"

    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_on_hand"] == "0.000"
    assert items[0]["qty_frozen"] == "0.000"


def test_pick_rejected_when_location_locked(client, auth_headers) -> None:
    masters = seed_masters(
        client, auth_headers, prefix="OUT", location_code="B-01-01", zone="B"
    )
    putaway_stock(client, auth_headers, masters, "2.000")
    pending = pending_outbound(client, auth_headers, masters, "2.000")
    approved = approve_outbound(client, auth_headers, pending, masters["location_id"])
    assert approved.status_code == 200
    order = approved.json()["data"]["order"]

    locked_id = masters["location_id"]
    set_location_lock_checker(lambda location_id: location_id == locked_id)
    response = pick_outbound(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=locked_id,
        qty_pick="1.000",
        idempotency_key=f"lock-{uuid4().hex}",
    )
    assert response.status_code == 409
    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_on_hand"] == "2.000"
    assert items[0]["qty_frozen"] == "2.000"


def test_done_order_cannot_be_edited(client, auth_headers) -> None:
    masters = seed_masters(
        client, auth_headers, prefix="OUT", location_code="B-01-01", zone="B"
    )
    putaway_stock(client, auth_headers, masters, "1.000")
    pending = pending_outbound(client, auth_headers, masters, "1.000")
    approved = approve_outbound(client, auth_headers, pending, masters["location_id"])
    order = approved.json()["data"]["order"]
    pick = pick_outbound(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_pick="1.000",
        idempotency_key=f"done-{uuid4().hex}",
    )
    assert pick.status_code == 200
    assert pick.json()["data"]["order"]["status"] == "done"
    edited = client.patch(
        f"/api/v1/outbound-orders/{order['id']}",
        headers=auth_headers,
        json={"remark": "改不得"},
    )
    assert edited.status_code == 409
