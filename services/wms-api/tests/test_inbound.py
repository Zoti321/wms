"""入库 HTTP 次缝：建单 → 审核 → 部分上架 → 库存可见；取消/锁/幂等。"""

from __future__ import annotations

from uuid import uuid4

from app.inventory.application.lock import set_location_lock_checker
from tests.http_scenarios import (
    approved_inbound,
    idem_headers,
    list_balances,
    list_ledgers,
    putaway,
    seed_masters,
)


def test_inbound_write_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/inbound-orders",
        json={
            "warehouse_id": 1,
            "order_type": "purchase",
            "lines": [{"sku_id": 1, "planned_qty": "1"}],
        },
    )
    assert response.status_code == 401


def test_inbound_putaway_flow_updates_inventory(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="10.000")
    line_id = order["lines"][0]["id"]

    first = putaway(
        client,
        auth_headers,
        order["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put="4.000",
        idempotency_key=f"p1-{uuid4().hex}",
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["order"]["status"] == "putaway"
    assert first.json()["data"]["order"]["lines"][0]["putaway_qty"] == "4.000"

    second = putaway(
        client,
        auth_headers,
        order["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put="6.000",
        idempotency_key=f"p2-{uuid4().hex}",
    )
    assert second.status_code == 200, second.text
    assert second.json()["data"]["order"]["status"] == "done"

    items = list_balances(
        client,
        auth_headers,
        warehouse_id=masters["warehouse_id"],
        sku_id=masters["sku_id"],
    )
    assert len(items) == 1
    assert items[0]["qty_on_hand"] == "10.000"
    assert items[0]["qty_available"] == "10.000"
    assert items[0]["qty_frozen"] == "0.000"

    assert len(list_ledgers(client, auth_headers, ref_line_id=line_id)) == 2


def test_putaway_idempotent_key_replays(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="5.000")
    line_id = order["lines"][0]["id"]
    key = f"idem-{uuid4().hex}"
    headers = idem_headers(auth_headers, key)

    r1 = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers=headers,
        json={"line_id": line_id, "location_id": masters["location_id"], "qty": "5.000"},
    )
    r2 = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers=headers,
        json={"line_id": line_id, "location_id": masters["location_id"], "qty": "5.000"},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["data"]["replayed"] is True

    items = list_balances(client, auth_headers, warehouse_id=masters["warehouse_id"])
    assert items[0]["qty_on_hand"] == "5.000"


def test_cancel_without_putaway_ok_but_after_putaway_rejected(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="3.000")
    cancelled = client.post(
        f"/api/v1/inbound-orders/{order['id']}/cancel",
        headers=auth_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    order2 = approved_inbound(client, auth_headers, masters, qty_planned="3.000")
    putaway(
        client,
        auth_headers,
        order2["id"],
        line_id=order2["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="1.000",
        idempotency_key=f"c-{uuid4().hex}",
    )
    blocked = client.post(
        f"/api/v1/inbound-orders/{order2['id']}/cancel",
        headers=auth_headers,
    )
    assert blocked.status_code == 409


def test_putaway_rejected_when_location_locked(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="2.000")
    locked_id = masters["location_id"]
    set_location_lock_checker(lambda location_id: location_id == locked_id)

    response = putaway(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=locked_id,
        qty_put="1.000",
        idempotency_key=f"lock-{uuid4().hex}",
    )
    assert response.status_code == 409
    assert (
        list_balances(
            client,
            auth_headers,
            warehouse_id=masters["warehouse_id"],
        )
        == []
    )


def test_done_order_cannot_be_edited(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="1.000")
    put = putaway(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="1.000",
        idempotency_key=f"done-{uuid4().hex}",
    )
    assert put.status_code == 200
    assert put.json()["data"]["putaway_record_id"] > 0
    edited = client.patch(
        f"/api/v1/inbound-orders/{order['id']}",
        headers=auth_headers,
        json={"remark": "改不得"},
    )
    assert edited.status_code == 409


def test_putaway_fails_when_inventory_increase_fails(
    client, auth_headers, monkeypatch
) -> None:
    masters = seed_masters(client, auth_headers, prefix="IN")
    order = approved_inbound(client, auth_headers, masters, qty_planned="2.000")

    def boom(*_args, **_kwargs):
        from app.inventory.application.inventory_service import InventoryError

        raise InventoryError("模拟记账失败")

    monkeypatch.setattr(
        "app.inbound.application.inbound_service.inv.increase", boom
    )
    response = putaway(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="1.000",
        idempotency_key=f"fail-{uuid4().hex}",
    )
    assert response.status_code == 409
    detail = client.get(
        f"/api/v1/inbound-orders/{order['id']}", headers=auth_headers
    ).json()["data"]
    assert detail["status"] == "approved"
    assert detail["lines"][0]["putaway_qty"] == "0.000"
    assert (
        list_balances(
            client,
            auth_headers,
            warehouse_id=masters["warehouse_id"],
        )
        == []
    )
