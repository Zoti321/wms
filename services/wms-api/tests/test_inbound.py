"""入库 HTTP 次缝：建单 → 审核 → 部分上架 → 库存可见；取消/锁/幂等。"""

from __future__ import annotations

from uuid import uuid4

from app.inventory.application.lock import set_location_lock_checker


def _seed_masters(client, auth_headers) -> dict[str, int]:
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": "WH-IN", "name": "入库仓"},
    ).json()["data"]
    sku = client.post(
        "/api/v1/skus",
        headers=auth_headers,
        json={"sku_code": "SKU-IN", "name": "入库商品", "unit": "PCS"},
    ).json()["data"]
    loc = client.post(
        "/api/v1/locations",
        headers=auth_headers,
        json={
            "warehouse_id": wh["id"],
            "location_code": "A-01-01",
            "zone": "A",
            "aisle": "01",
            "bin": "01",
        },
    ).json()["data"]
    return {"warehouse_id": wh["id"], "sku_id": sku["id"], "location_id": loc["id"]}


def _create_approved_order(client, auth_headers, masters: dict[str, int], qty: str = "10.000"):
    created = client.post(
        "/api/v1/inbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty}],
        },
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/inbound-orders/{order_id}/submit", headers=auth_headers).status_code == 200
    approved = client.post(f"/api/v1/inbound-orders/{order_id}/approve", headers=auth_headers)
    assert approved.status_code == 200
    return approved.json()["data"]


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
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="10.000")
    line_id = order["lines"][0]["id"]

    first = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"p1-{uuid4().hex}"},
        json={"line_id": line_id, "location_id": masters["location_id"], "qty": "4.000"},
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["order"]["status"] == "putaway"
    assert first.json()["data"]["order"]["lines"][0]["putaway_qty"] == "4.000"

    second = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"p2-{uuid4().hex}"},
        json={"line_id": line_id, "location_id": masters["location_id"], "qty": "6.000"},
    )
    assert second.status_code == 200, second.text
    assert second.json()["data"]["order"]["status"] == "done"

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"], "sku_id": masters["sku_id"]},
    )
    assert balances.status_code == 200
    items = balances.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["qty_on_hand"] == "10.000"
    assert items[0]["qty_available"] == "10.000"
    assert items[0]["qty_frozen"] == "0.000"

    ledgers = client.get(
        "/api/v1/inventories/ledgers",
        headers=auth_headers,
        params={"ref_line_id": line_id},
    )
    assert ledgers.status_code == 200
    assert len(ledgers.json()["data"]["items"]) == 2


def test_putaway_idempotent_key_replays(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="5.000")
    line_id = order["lines"][0]["id"]
    key = f"idem-{uuid4().hex}"
    payload = {"line_id": line_id, "location_id": masters["location_id"], "qty": "5.000"}
    headers = {**auth_headers, "Idempotency-Key": key}

    r1 = client.post(f"/api/v1/inbound-orders/{order['id']}/putaway", headers=headers, json=payload)
    r2 = client.post(f"/api/v1/inbound-orders/{order['id']}/putaway", headers=headers, json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["data"]["replayed"] is True

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances[0]["qty_on_hand"] == "5.000"


def test_cancel_without_putaway_ok_but_after_putaway_rejected(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="3.000")
    cancelled = client.post(
        f"/api/v1/inbound-orders/{order['id']}/cancel",
        headers=auth_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    order2 = _create_approved_order(client, auth_headers, masters, qty="3.000")
    client.post(
        f"/api/v1/inbound-orders/{order2['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"c-{uuid4().hex}"},
        json={
            "line_id": order2["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    blocked = client.post(
        f"/api/v1/inbound-orders/{order2['id']}/cancel",
        headers=auth_headers,
    )
    assert blocked.status_code == 409


def test_putaway_rejected_when_location_locked(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="2.000")
    locked_id = masters["location_id"]
    set_location_lock_checker(lambda location_id: location_id == locked_id)

    response = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"lock-{uuid4().hex}"},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": locked_id,
            "qty": "1.000",
        },
    )
    assert response.status_code == 409
    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances == []


def test_done_order_cannot_be_edited(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="1.000")
    put = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"done-{uuid4().hex}"},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
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
    masters = _seed_masters(client, auth_headers)
    order = _create_approved_order(client, auth_headers, masters, qty="2.000")

    def boom(*_args, **_kwargs):
        from app.inventory.application.inventory_service import InventoryError

        raise InventoryError("模拟记账失败")

    monkeypatch.setattr(
        "app.inbound.application.inbound_service.inv.increase", boom
    )
    response = client.post(
        f"/api/v1/inbound-orders/{order['id']}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"fail-{uuid4().hex}"},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    assert response.status_code == 409
    detail = client.get(
        f"/api/v1/inbound-orders/{order['id']}", headers=auth_headers
    ).json()["data"]
    assert detail["status"] == "approved"
    assert detail["lines"][0]["putaway_qty"] == "0.000"
    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances == []
