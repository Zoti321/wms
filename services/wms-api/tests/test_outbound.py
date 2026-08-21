"""出库 HTTP 次缝：建单 → 审核分配 → 部分拣货 → 取消未拣；不足整单失败；锁/幂等。"""

from __future__ import annotations

from uuid import uuid4

from app.inventory.application.lock import set_location_lock_checker


def _seed_masters(client, auth_headers) -> dict[str, int]:
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": "WH-OUT", "name": "出库仓"},
    ).json()["data"]
    sku = client.post(
        "/api/v1/skus",
        headers=auth_headers,
        json={"sku_code": "SKU-OUT", "name": "出库商品", "unit": "PCS"},
    ).json()["data"]
    loc = client.post(
        "/api/v1/locations",
        headers=auth_headers,
        json={
            "warehouse_id": wh["id"],
            "location_code": "B-01-01",
            "zone": "B",
            "aisle": "01",
            "bin": "01",
        },
    ).json()["data"]
    return {"warehouse_id": wh["id"], "sku_id": sku["id"], "location_id": loc["id"]}


def _putaway_stock(client, auth_headers, masters: dict[str, int], qty: str) -> None:
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
    assert (
        client.post(f"/api/v1/inbound-orders/{order_id}/submit", headers=auth_headers).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/inbound-orders/{order_id}/approve", headers=auth_headers
    )
    assert approved.status_code == 200
    line_id = approved.json()["data"]["lines"][0]["id"]
    put = client.post(
        f"/api/v1/inbound-orders/{order_id}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"in-{uuid4().hex}"},
        json={
            "line_id": line_id,
            "location_id": masters["location_id"],
            "qty": qty,
        },
    )
    assert put.status_code == 200, put.text


def _create_pending_outbound(
    client, auth_headers, masters: dict[str, int], qty: str = "10.000"
) -> dict:
    created = client.post(
        "/api/v1/outbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "sales",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty}],
        },
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["data"]["id"]
    submitted = client.post(
        f"/api/v1/outbound-orders/{order_id}/submit", headers=auth_headers
    )
    assert submitted.status_code == 200
    return submitted.json()["data"]


def _approve(
    client,
    auth_headers,
    order: dict,
    location_id: int,
    *,
    key: str | None = None,
):
    return client.post(
        f"/api/v1/outbound-orders/{order['id']}/approve",
        headers={**auth_headers, "Idempotency-Key": key or f"ap-{uuid4().hex}"},
        json={
            "allocations": [
                {"line_id": order["lines"][0]["id"], "location_id": location_id}
            ]
        },
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
    masters = _seed_masters(client, auth_headers)
    _putaway_stock(client, auth_headers, masters, "10.000")

    pending = _create_pending_outbound(client, auth_headers, masters, "10.000")
    approved = _approve(client, auth_headers, pending, masters["location_id"])
    assert approved.status_code == 200, approved.text
    order = approved.json()["data"]["order"]
    assert order["status"] == "approved"
    assert order["lines"][0]["allocated_qty"] == "10.000"

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances[0]["qty_on_hand"] == "10.000"
    assert balances[0]["qty_frozen"] == "10.000"
    assert balances[0]["qty_available"] == "0.000"

    line_id = order["lines"][0]["id"]
    pick1 = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers={**auth_headers, "Idempotency-Key": f"pk1-{uuid4().hex}"},
        json={
            "line_id": line_id,
            "location_id": masters["location_id"],
            "qty": "4.000",
        },
    )
    assert pick1.status_code == 200, pick1.text
    assert pick1.json()["data"]["order"]["status"] == "picking"
    assert pick1.json()["data"]["order"]["lines"][0]["picked_qty"] == "4.000"

    cancelled = client.post(
        f"/api/v1/outbound-orders/{order['id']}/cancel",
        headers={**auth_headers, "Idempotency-Key": f"cx-{uuid4().hex}"},
    )
    assert cancelled.status_code == 200, cancelled.text
    # 已有实扣 → 已完成；已实扣 4 保留；未拣 6 释放
    assert cancelled.json()["data"]["order"]["status"] == "done"
    assert "退货入库" in (cancelled.json()["data"].get("note") or "")
    assert cancelled.json()["data"]["order"]["lines"][0]["picked_qty"] == "4.000"
    assert cancelled.json()["data"]["order"]["lines"][0]["allocated_qty"] == "4.000"

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances[0]["qty_on_hand"] == "6.000"
    assert balances[0]["qty_frozen"] == "0.000"
    assert balances[0]["qty_available"] == "6.000"

    ledgers = client.get(
        "/api/v1/inventories/ledgers",
        headers=auth_headers,
        params={"ref_line_id": line_id},
    ).json()["data"]["items"]
    types = [row["ref_type"] for row in ledgers]
    assert "ALLOCATE" in types
    assert "PICK" in types
    assert "RELEASE" in types


def test_approve_insufficient_fails_without_reservation(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    _putaway_stock(client, auth_headers, masters, "3.000")
    pending = _create_pending_outbound(client, auth_headers, masters, "5.000")

    response = _approve(client, auth_headers, pending, masters["location_id"])
    assert response.status_code == 400

    detail = client.get(
        f"/api/v1/outbound-orders/{pending['id']}", headers=auth_headers
    ).json()["data"]
    assert detail["status"] == "pending"
    assert detail["lines"][0]["allocated_qty"] == "0.000"

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances[0]["qty_frozen"] == "0.000"
    assert balances[0]["qty_available"] == "3.000"


def test_approve_and_pick_idempotent(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    _putaway_stock(client, auth_headers, masters, "5.000")
    pending = _create_pending_outbound(client, auth_headers, masters, "5.000")
    key = f"idem-ap-{uuid4().hex}"

    r1 = _approve(client, auth_headers, pending, masters["location_id"], key=key)
    r2 = _approve(client, auth_headers, pending, masters["location_id"], key=key)
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
        headers={**auth_headers, "Idempotency-Key": pick_key},
        json=payload,
    )
    p2 = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers={**auth_headers, "Idempotency-Key": pick_key},
        json=payload,
    )
    assert p1.status_code == 200
    assert p2.status_code == 200
    assert p2.json()["data"]["replayed"] is True
    assert p1.json()["data"]["order"]["status"] == "done"

    balances = client.get(
        "/api/v1/inventories",
        headers=auth_headers,
        params={"warehouse_id": masters["warehouse_id"]},
    ).json()["data"]["items"]
    assert balances[0]["qty_on_hand"] == "0.000"
    assert balances[0]["qty_frozen"] == "0.000"


def test_pick_rejected_when_location_locked(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    _putaway_stock(client, auth_headers, masters, "2.000")
    pending = _create_pending_outbound(client, auth_headers, masters, "2.000")
    approved = _approve(client, auth_headers, pending, masters["location_id"])
    assert approved.status_code == 200
    order = approved.json()["data"]["order"]

    locked_id = masters["location_id"]
    set_location_lock_checker(lambda location_id: location_id == locked_id)
    response = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
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
    assert balances[0]["qty_on_hand"] == "2.000"
    assert balances[0]["qty_frozen"] == "2.000"


def test_done_order_cannot_be_edited(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    _putaway_stock(client, auth_headers, masters, "1.000")
    pending = _create_pending_outbound(client, auth_headers, masters, "1.000")
    approved = _approve(client, auth_headers, pending, masters["location_id"])
    order = approved.json()["data"]["order"]
    pick = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers={**auth_headers, "Idempotency-Key": f"done-{uuid4().hex}"},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    assert pick.status_code == 200
    assert pick.json()["data"]["order"]["status"] == "done"
    edited = client.patch(
        f"/api/v1/outbound-orders/{order['id']}",
        headers=auth_headers,
        json={"remark": "改不得"},
    )
    assert edited.status_code == 409
