"""取消原因字典与 cancel 端点契约。"""

from __future__ import annotations

from uuid import uuid4

from tests.http_scenarios import (
    create_inbound,
    idem_headers,
    seed_masters,
    start_stocktake,
)


def test_inbound_cancel_without_reason_still_ok(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="CR")
    order = create_inbound(client, auth_headers, masters, "1.000")

    response = client.post(
        f"/api/v1/inbound-orders/{order['id']}/cancel",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"
    assert response.json()["data"]["remark"] is None


def test_inbound_cancel_with_valid_reason_appends_remark(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="CR")
    order = create_inbound(client, auth_headers, masters, "1.000")

    response = client.post(
        f"/api/v1/inbound-orders/{order['id']}/cancel",
        headers=auth_headers,
        json={"cancel_reason_code": "customer_cancel"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"
    assert data["remark"] == "[取消原因: 客户取消]"


def test_inbound_cancel_with_invalid_reason_returns_422(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="CR")
    order = create_inbound(client, auth_headers, masters, "1.000")

    response = client.post(
        f"/api/v1/inbound-orders/{order['id']}/cancel",
        headers=auth_headers,
        json={"cancel_reason_code": "not_a_reason"},
    )
    assert response.status_code == 422


def test_dictionary_list_filters_by_inbound_order_type(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/dictionaries",
        headers=auth_headers,
        params={"dict_type": "inbound_order_type", "page": 1, "page_size": 100},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) >= 2
    assert all(item["dict_type"] == "inbound_order_type" for item in items)
    codes = {item["code"] for item in items}
    assert "purchase" in codes
    assert "return" in codes


def test_dictionary_list_outbound_order_type(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/dictionaries",
        headers=auth_headers,
        params={"dict_type": "outbound_order_type", "page": 1, "page_size": 100},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    codes = {item["code"] for item in items}
    assert "sales" in codes
    assert "material" in codes


def test_outbound_cancel_with_reason(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="CR")
    create = client.post(
        "/api/v1/outbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "sales",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
        },
    )
    assert create.status_code == 200
    order_id = create.json()["data"]["id"]

    response = client.post(
        f"/api/v1/outbound-orders/{order_id}/cancel",
        headers=idem_headers(auth_headers, f"cr-out-{uuid4().hex}"),
        json={"cancel_reason_code": "stock_shortage"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["order"]["remark"] == "[取消原因: 库存不足]"


def test_stocktake_cancel_with_reason(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="CR")
    order = start_stocktake(client, auth_headers, masters["warehouse_id"])

    response = client.post(
        f"/api/v1/stocktakes/{order['id']}/cancel",
        headers=idem_headers(auth_headers, f"cr-st-cancel-{uuid4().hex}"),
        json={"cancel_reason_code": "customer_cancel"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["order"]["remark"] == "[取消原因: 客户取消]"
