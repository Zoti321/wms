"""入/出/盘点单据列表 HTTP：筛选、分页、鉴权。"""

from __future__ import annotations

from uuid import uuid4

from tests.http_scenarios import (
    create_inbound,
    create_outbound,
    data_ok,
    login,
    pending_outbound,
    seed_masters,
    submit_inbound,
)


def _list_inbound(client, headers, **params):
    return client.get("/api/v1/inbound-orders", headers=headers, params=params)


def _list_outbound(client, headers, **params):
    return client.get("/api/v1/outbound-orders", headers=headers, params=params)


def _list_stocktake(client, headers, **params):
    return client.get("/api/v1/stocktakes", headers=headers, params=params)


def _assert_list_envelope(data: dict, *, page: int, page_size: int) -> None:
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["page"] == page
    assert data["page_size"] == page_size
    assert isinstance(data["total"], int)
    assert data["total"] >= len(data["items"])


def test_inbound_list_requires_auth(client) -> None:
    assert client.get("/api/v1/inbound-orders").status_code == 401


def test_outbound_list_requires_auth(client) -> None:
    assert client.get("/api/v1/outbound-orders").status_code == 401


def test_stocktake_list_requires_auth(client) -> None:
    assert client.get("/api/v1/stocktakes").status_code == 401


def test_viewer_can_list_orders(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LST", with_location=False)
    create_inbound(client, auth_headers, masters, "1.000")
    viewer = login(client, "viewer")

    for list_fn in (_list_inbound, _list_outbound, _list_stocktake):
        payload = data_ok(list_fn(client, viewer))
        _assert_list_envelope(payload, page=1, page_size=20)


def test_inbound_list_filter_and_pagination(client, auth_headers) -> None:
    masters_a = seed_masters(client, auth_headers, prefix="LIA", with_location=False)
    masters_b = seed_masters(client, auth_headers, prefix="LIB", with_location=False)

    draft_a = create_inbound(client, auth_headers, masters_a, "1.000")
    pending_b = create_inbound(client, auth_headers, masters_b, "2.000")
    submit_inbound(client, auth_headers, pending_b["id"])

    all_items = data_ok(_list_inbound(client, auth_headers))
    _assert_list_envelope(all_items, page=1, page_size=20)
    assert all_items["total"] >= 2
    ids = {item["id"] for item in all_items["items"]}
    assert draft_a["id"] in ids
    assert pending_b["id"] in ids

    by_wh = data_ok(
        _list_inbound(
            client,
            auth_headers,
            warehouse_id=masters_a["warehouse_id"],
        )
    )
    assert all(item["warehouse_id"] == masters_a["warehouse_id"] for item in by_wh["items"])
    assert any(item["id"] == draft_a["id"] for item in by_wh["items"])
    assert all(item["id"] != pending_b["id"] for item in by_wh["items"])

    by_status = data_ok(
        _list_inbound(client, auth_headers, status="pending")
    )
    assert all(item["status"] == "pending" for item in by_status["items"])
    assert any(item["id"] == pending_b["id"] for item in by_status["items"])
    assert all(item["id"] != draft_a["id"] for item in by_status["items"])

    page1 = data_ok(_list_inbound(client, auth_headers, page=1, page_size=1))
    _assert_list_envelope(page1, page=1, page_size=1)
    assert len(page1["items"]) == 1
    assert page1["total"] >= 2

    empty_page = data_ok(
        _list_inbound(client, auth_headers, page=999, page_size=20)
    )
    assert empty_page["items"] == []
    assert empty_page["total"] >= 2

    assert _list_inbound(client, auth_headers, page=0).status_code == 422
    assert _list_inbound(client, auth_headers, page_size=101).status_code == 422

    detail = data_ok(
        client.get(
            f"/api/v1/inbound-orders/{draft_a['id']}", headers=auth_headers
        )
    )
    list_row = next(item for item in all_items["items"] if item["id"] == draft_a["id"])
    for key in ("id", "order_no", "warehouse_id", "order_type", "status", "created_at"):
        assert list_row[key] == detail[key]
    assert list_row["supplier_id"] == detail["supplier_id"]


def _create_inbound_with(
    client,
    headers: dict[str, str],
    masters: dict,
    *,
    order_no: str,
    order_type: str = "purchase",
) -> dict:
    return data_ok(
        client.post(
            "/api/v1/inbound-orders",
            headers=headers,
            json={
                "warehouse_id": masters["warehouse_id"],
                "order_type": order_type,
                "order_no": order_no,
                "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
            },
        )
    )


def _create_outbound_with(
    client,
    headers: dict[str, str],
    masters: dict,
    *,
    order_no: str,
    order_type: str = "sales",
) -> dict:
    return data_ok(
        client.post(
            "/api/v1/outbound-orders",
            headers=headers,
            json={
                "warehouse_id": masters["warehouse_id"],
                "order_type": order_type,
                "order_no": order_no,
                "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
            },
        )
    )


def test_inbound_list_filter_by_order_no_and_type(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LNO", with_location=False)
    purchase = _create_inbound_with(
        client,
        auth_headers,
        masters,
        order_no="INB-FILTER-PUR-001",
        order_type="purchase",
    )
    other = _create_inbound_with(
        client,
        auth_headers,
        masters,
        order_no="INB-FILTER-RET-002",
        order_type="return",
    )

    by_no = data_ok(
        _list_inbound(client, auth_headers, order_no="FILTER-PUR")
    )
    ids = {item["id"] for item in by_no["items"]}
    assert purchase["id"] in ids
    assert other["id"] not in ids
    assert by_no["total"] >= 1

    by_type = data_ok(
        _list_inbound(
            client,
            auth_headers,
            warehouse_id=masters["warehouse_id"],
            order_type="return",
        )
    )
    assert all(item["order_type"] == "return" for item in by_type["items"])
    assert any(item["id"] == other["id"] for item in by_type["items"])
    assert all(item["id"] != purchase["id"] for item in by_type["items"])

    combined = data_ok(
        _list_inbound(
            client,
            auth_headers,
            order_no="FILTER-RET",
            order_type="return",
            status="draft",
        )
    )
    assert len(combined["items"]) == 1
    assert combined["items"][0]["id"] == other["id"]
    assert combined["total"] == 1

    assert _list_inbound(client, auth_headers, order_type="invalid").status_code == 400


def test_outbound_list_filter_by_order_no_and_type(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LNOU", with_location=False)
    sales = _create_outbound_with(
        client,
        auth_headers,
        masters,
        order_no="OUT-FILTER-SAL-001",
        order_type="sales",
    )
    material = _create_outbound_with(
        client,
        auth_headers,
        masters,
        order_no="OUT-FILTER-MAT-002",
        order_type="material",
    )

    by_no = data_ok(
        _list_outbound(client, auth_headers, order_no="FILTER-SAL")
    )
    ids = {item["id"] for item in by_no["items"]}
    assert sales["id"] in ids
    assert material["id"] not in ids

    by_type = data_ok(
        _list_outbound(
            client,
            auth_headers,
            warehouse_id=masters["warehouse_id"],
            order_type="material",
        )
    )
    assert all(item["order_type"] == "material" for item in by_type["items"])
    assert any(item["id"] == material["id"] for item in by_type["items"])

    assert _list_outbound(client, auth_headers, order_type="invalid").status_code == 400


def test_inbound_list_sorted_by_created_at_desc(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LIS", with_location=False)
    first = create_inbound(client, auth_headers, masters, "1.000")
    second = create_inbound(client, auth_headers, masters, "2.000")
    payload = data_ok(_list_inbound(client, auth_headers, warehouse_id=masters["warehouse_id"]))
    ids = [item["id"] for item in payload["items"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_outbound_list_filter_by_status(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LOU", with_location=False)
    draft = create_outbound(client, auth_headers, masters, "1.000")
    pending = pending_outbound(client, auth_headers, masters, "2.000")

    by_pending = data_ok(_list_outbound(client, auth_headers, status="pending"))
    pending_ids = {item["id"] for item in by_pending["items"]}
    assert pending["id"] in pending_ids
    assert draft["id"] not in pending_ids

    row = next(item for item in by_pending["items"] if item["id"] == pending["id"])
    detail = data_ok(
        client.get(f"/api/v1/outbound-orders/{pending['id']}", headers=auth_headers)
    )
    for key in ("id", "order_no", "warehouse_id", "order_type", "status", "created_at"):
        assert row[key] == detail[key]


def test_stocktake_list_by_warehouse(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="LSTK", extra_location=True)
    created = client.post(
        "/api/v1/stocktakes",
        headers={**auth_headers, "Idempotency-Key": f"st-list-{uuid4().hex}"},
        json={"warehouse_id": masters["warehouse_id"], "zone": "A"},
    )
    assert created.status_code == 200, created.text
    order = created.json()["data"]["order"]

    payload = data_ok(
        _list_stocktake(client, auth_headers, warehouse_id=masters["warehouse_id"])
    )
    assert any(item["id"] == order["id"] for item in payload["items"])
    row = next(item for item in payload["items"] if item["id"] == order["id"])
    detail = data_ok(
        client.get(f"/api/v1/stocktakes/{order['id']}", headers=auth_headers)
    )
    for key in ("id", "order_no", "warehouse_id", "status", "created_at"):
        assert row[key] == detail[key]

    other_wh = data_ok(
        _list_stocktake(client, auth_headers, warehouse_id=999_999)
    )
    assert other_wh["items"] == []
    assert other_wh["total"] == 0
