"""只读列表 HTTP：11 个端点统一分页、筛选与鉴权。"""

from __future__ import annotations

import pytest

from tests.http_scenarios import (
    approved_inbound,
    data_ok,
    login,
    putaway_ok,
    seed_masters,
)

READONLY_LIST_ENDPOINTS = (
    "/api/v1/warehouses",
    "/api/v1/skus",
    "/api/v1/locations",
    "/api/v1/suppliers",
    "/api/v1/customers",
    "/api/v1/inventories",
    "/api/v1/inventories/ledgers",
    "/api/v1/inventories/alerts",
    "/api/v1/operation-logs",
    "/api/v1/dictionaries",
    "/api/v1/users",
)


def _assert_list_envelope(data: dict, *, page: int, page_size: int) -> None:
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["page"] == page
    assert data["page_size"] == page_size
    assert isinstance(data["total"], int)
    assert data["total"] >= len(data["items"])


@pytest.mark.parametrize("path", READONLY_LIST_ENDPOINTS)
def test_readonly_list_requires_auth(client, path: str) -> None:
    assert client.get(path).status_code == 401


def test_viewer_can_list_readonly_endpoints(client, auth_headers) -> None:
    viewer = login(client, "viewer")
    forbidden_for_viewer = {"/api/v1/users", "/api/v1/operation-logs"}
    for path in READONLY_LIST_ENDPOINTS:
        if path in forbidden_for_viewer:
            assert client.get(path, headers=viewer).status_code == 403
            continue
        payload = data_ok(client.get(path, headers=viewer))
        _assert_list_envelope(payload, page=1, page_size=20)


def test_catalog_list_filter_and_pagination(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="RLC", with_location=True)

    payload = data_ok(
        client.get(
            "/api/v1/skus",
            headers=auth_headers,
            params={"code": masters["sku"]["sku_code"], "status": 1},
        )
    )
    _assert_list_envelope(payload, page=1, page_size=20)
    assert any(item["id"] == masters["sku_id"] for item in payload["items"])

    selectable = data_ok(
        client.get(
            "/api/v1/locations",
            headers=auth_headers,
            params={
                "warehouse_id": masters["warehouse_id"],
                "selectable": True,
                "page": 1,
                "page_size": 1,
            },
        )
    )
    _assert_list_envelope(selectable, page=1, page_size=1)
    assert len(selectable["items"]) == 1

    assert (
        client.get("/api/v1/warehouses", headers=auth_headers, params={"page": 0}).status_code
        == 422
    )
    assert (
        client.get(
            "/api/v1/warehouses", headers=auth_headers, params={"page_size": 101}
        ).status_code
        == 422
    )


def test_inventory_list_filter_and_pagination(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="RLI", with_location=True)
    order = approved_inbound(client, auth_headers, masters, qty_planned="3.000")
    putaway_ok(
        client,
        auth_headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="3.000",
    )
    line_id = order["lines"][0]["id"]

    balances = data_ok(
        client.get(
            "/api/v1/inventories",
            headers=auth_headers,
            params={"warehouse_id": masters["warehouse_id"], "sku_id": masters["sku_id"]},
        )
    )
    _assert_list_envelope(balances, page=1, page_size=20)
    assert len(balances["items"]) >= 1

    ledgers = data_ok(
        client.get(
            "/api/v1/inventories/ledgers",
            headers=auth_headers,
            params={"ref_line_id": line_id, "page": 1, "page_size": 10},
        )
    )
    _assert_list_envelope(ledgers, page=1, page_size=10)
    assert all(item["ref_line_id"] == line_id for item in ledgers["items"])
    assert ledgers["total"] >= 1

    page1 = data_ok(
        client.get(
            "/api/v1/inventories/ledgers",
            headers=auth_headers,
            params={"ref_line_id": line_id, "page": 1, "page_size": 1},
        )
    )
    page2 = data_ok(
        client.get(
            "/api/v1/inventories/ledgers",
            headers=auth_headers,
            params={"ref_line_id": line_id, "page": 2, "page_size": 1},
        )
    )
    if page1["total"] >= 2:
        assert page1["items"][0]["id"] != page2["items"][0]["id"]


def test_platform_list_pagination(client, auth_headers) -> None:
    logs = data_ok(client.get("/api/v1/operation-logs", headers=auth_headers))
    _assert_list_envelope(logs, page=1, page_size=20)

    dictionaries = data_ok(
        client.get("/api/v1/dictionaries", headers=auth_headers, params={"dict_type": "unit"})
    )
    _assert_list_envelope(dictionaries, page=1, page_size=20)

    users = data_ok(client.get("/api/v1/users", headers=auth_headers))
    _assert_list_envelope(users, page=1, page_size=20)
    assert users["total"] >= 4

    empty_page = data_ok(
        client.get("/api/v1/users", headers=auth_headers, params={"page": 999, "page_size": 20})
    )
    assert empty_page["items"] == []
    assert empty_page["total"] >= 4
