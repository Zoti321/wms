"""M1 主数据 Catalog HTTP 行为（外部缝）：创建 → 查询 → 停用 → 可选用列表。"""

from __future__ import annotations


def test_create_warehouse_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/warehouses",
        json={"warehouse_code": "WH-01", "name": "主仓"},
    )
    assert response.status_code == 401


def test_warehouse_create_get_list_deactivate_flow(client, auth_headers) -> None:
    created = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": "WH-01", "name": "主仓"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["code"] == 0
    warehouse = body["data"]
    assert warehouse["warehouse_code"] == "WH-01"
    assert warehouse["name"] == "主仓"
    assert warehouse["status"] == 1
    warehouse_id = warehouse["id"]

    detail = client.get(f"/api/v1/warehouses/{warehouse_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == warehouse_id

    listed = client.get(
        "/api/v1/warehouses",
        headers=auth_headers,
        params={"status": 1, "code": "WH"},
    )
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert any(item["id"] == warehouse_id for item in items)

    deactivated = client.post(
        f"/api/v1/warehouses/{warehouse_id}/deactivate",
        headers=auth_headers,
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["status"] == 0

    selectable = client.get(
        "/api/v1/warehouses",
        headers=auth_headers,
        params={"selectable": True},
    )
    assert selectable.status_code == 200
    assert all(item["id"] != warehouse_id for item in selectable.json()["data"]["items"])


def test_warehouse_deactivate_blocked_when_active_locations(client, auth_headers) -> None:
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": "WH-BLOCK", "name": "有库位仓"},
    ).json()["data"]
    client.post(
        "/api/v1/locations",
        headers=auth_headers,
        json={
            "warehouse_id": wh["id"],
            "location_code": "B-01-01",
            "zone": "B",
            "aisle": "01",
            "bin": "01",
        },
    )
    blocked = client.post(
        f"/api/v1/warehouses/{wh['id']}/deactivate",
        headers=auth_headers,
    )
    assert blocked.status_code == 409


def test_sku_create_update_deactivate_and_selectable(client, auth_headers) -> None:
    created = client.post(
        "/api/v1/skus",
        headers=auth_headers,
        json={
            "sku_code": "SKU-001",
            "name": "螺栓 M8",
            "unit": "PCS",
            "spec": "M8x20",
            "barcode": "6900001",
            "safety_stock": "10.000",
        },
    )
    assert created.status_code == 200
    sku = created.json()["data"]
    assert sku["sku_code"] == "SKU-001"
    assert sku["safety_stock"] == "10.000"
    assert sku["status"] == 1
    sku_id = sku["id"]

    updated = client.patch(
        f"/api/v1/skus/{sku_id}",
        headers=auth_headers,
        json={"name": "螺栓 M8 镀锌", "safety_stock": "20.500"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "螺栓 M8 镀锌"
    assert updated.json()["data"]["safety_stock"] == "20.500"

    client.post(f"/api/v1/skus/{sku_id}/deactivate", headers=auth_headers)

    selectable = client.get(
        "/api/v1/skus",
        headers=auth_headers,
        params={"selectable": True},
    )
    assert selectable.status_code == 200
    assert all(item["id"] != sku_id for item in selectable.json()["data"]["items"])

    all_list = client.get(
        "/api/v1/skus",
        headers=auth_headers,
        params={"code": "SKU-001"},
    )
    assert any(item["id"] == sku_id and item["status"] == 0 for item in all_list.json()["data"]["items"])


def test_sku_duplicate_code_rejected(client, auth_headers) -> None:
    payload = {"sku_code": "SKU-DUP", "name": "A", "unit": "PCS"}
    assert client.post("/api/v1/skus", headers=auth_headers, json=payload).status_code == 200
    dup = client.post("/api/v1/skus", headers=auth_headers, json=payload)
    assert dup.status_code == 409


def test_location_hierarchy_space_status_and_warehouse_filter(client, auth_headers) -> None:
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": "WH-LOC", "name": "库位仓"},
    ).json()["data"]

    created = client.post(
        "/api/v1/locations",
        headers=auth_headers,
        json={
            "warehouse_id": wh["id"],
            "location_code": "A-01-01",
            "zone": "A",
            "aisle": "01",
            "bin": "01",
        },
    )
    assert created.status_code == 200
    loc = created.json()["data"]
    assert loc["location_code"] == "A-01-01"
    assert loc["zone"] == "A"
    assert loc["aisle"] == "01"
    assert loc["bin"] == "01"
    assert loc["space_status"] == "idle"
    assert loc["status"] == 1
    loc_id = loc["id"]

    patched = client.patch(
        f"/api/v1/locations/{loc_id}",
        headers=auth_headers,
        json={"space_status": "frozen"},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["space_status"] == "frozen"

    filtered = client.get(
        "/api/v1/locations",
        headers=auth_headers,
        params={"warehouse_id": wh["id"], "selectable": True},
    )
    assert filtered.status_code == 200
    items = filtered.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == loc_id
    # 库位空间「冻结」≠ 库存冻结数量；字段名必须是 space_status
    assert "space_status" in items[0]
    assert "qty_frozen" not in items[0]

    client.post(f"/api/v1/locations/{loc_id}/deactivate", headers=auth_headers)
    selectable = client.get(
        "/api/v1/locations",
        headers=auth_headers,
        params={"warehouse_id": wh["id"], "selectable": True},
    )
    assert selectable.json()["data"]["items"] == []


def test_supplier_and_customer_deactivate_flow(client, auth_headers) -> None:
    supplier = client.post(
        "/api/v1/suppliers",
        headers=auth_headers,
        json={"supplier_code": "SUP-01", "name": "华东五金"},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["data"]["id"]

    customer = client.post(
        "/api/v1/customers",
        headers=auth_headers,
        json={"customer_code": "CUS-01", "name": "城南门店"},
    )
    assert customer.status_code == 200
    customer_id = customer.json()["data"]["id"]

    client.post(f"/api/v1/suppliers/{supplier_id}/deactivate", headers=auth_headers)
    client.post(f"/api/v1/customers/{customer_id}/deactivate", headers=auth_headers)

    suppliers = client.get(
        "/api/v1/suppliers",
        headers=auth_headers,
        params={"selectable": True},
    ).json()["data"]["items"]
    customers = client.get(
        "/api/v1/customers",
        headers=auth_headers,
        params={"selectable": True},
    ).json()["data"]["items"]
    assert all(item["id"] != supplier_id for item in suppliers)
    assert all(item["id"] != customer_id for item in customers)
