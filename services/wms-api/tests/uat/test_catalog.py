"""主数据验收：启用仓库/SKU/库位；停用 SKU 不可新开单；库位空间状态 ≠ 冻结数量。"""

from __future__ import annotations

from tests.uat.support import (
    data_err,
    data_ok,
    receive_purchase,
    seed_masters,
)


def test_系统管理员_可创建并启用默认仓库及关联SKU库位(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    warehouse = data_ok(
        uat_client.get(
            f"/api/v1/warehouses/{masters['warehouse_id']}",
            headers=tokens["admin"],
        )
    )
    assert warehouse["status"] == 1
    sku = data_ok(
        uat_client.get(f"/api/v1/skus/{masters['sku_id']}", headers=tokens["admin"])
    )
    assert sku["status"] == 1
    location = data_ok(
        uat_client.get(
            f"/api/v1/locations/{masters['location_id']}",
            headers=tokens["admin"],
        )
    )
    assert location["warehouse_id"] == masters["warehouse_id"]
    assert location["status"] == 1


def test_停用SKU后不可被新单据选用且历史单据仍可查(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    historical = receive_purchase(uat_client, tokens, masters, "2.000")

    deactivated = data_ok(
        uat_client.post(
            f"/api/v1/skus/{masters['sku_id']}/deactivate",
            headers=tokens["admin"],
        )
    )
    assert deactivated["status"] == 0

    selectable = data_ok(
        uat_client.get("/api/v1/skus", headers=tokens["admin"], params={"selectable": True})
    )["items"]
    assert all(item["id"] != masters["sku_id"] for item in selectable)

    denied = uat_client.post(
        "/api/v1/inbound-orders",
        headers=tokens["operator"],
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "1.000"}],
        },
    )
    data_err(denied, status=400)

    still_visible = data_ok(
        uat_client.get(
            f"/api/v1/inbound-orders/{historical['id']}",
            headers=tokens["operator"],
        )
    )
    assert still_visible["id"] == historical["id"]
    assert still_visible["lines"][0]["sku_id"] == masters["sku_id"]


def test_库位空间状态变更不影响库存冻结数量口径(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "4.000")

    patched = data_ok(
        uat_client.patch(
            f"/api/v1/locations/{masters['location_id']}",
            headers=tokens["admin"],
            json={"space_status": "frozen"},
        )
    )
    assert patched["space_status"] == "frozen"
    assert "qty_frozen" not in patched

    balances = data_ok(
        uat_client.get(
            "/api/v1/inventories",
            headers=tokens["viewer"],
            params={
                "warehouse_id": masters["warehouse_id"],
                "sku_id": masters["sku_id"],
            },
        )
    )["items"]
    assert balances[0]["qty_frozen"] == "0.000"
    assert balances[0]["qty_on_hand"] == "4.000"
    assert "space_status" not in balances[0]
