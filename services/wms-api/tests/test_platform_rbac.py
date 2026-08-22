"""M6：角色鉴权与操作日志 HTTP 外部缝。"""

from __future__ import annotations

from uuid import uuid4

from tests.conftest import SEED_PASSWORD


def _login(client, username: str, password: str = SEED_PASSWORD) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_masters(client, auth_headers) -> dict[str, int]:
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": f"WH-M6-{uuid4().hex[:6]}", "name": "鉴权仓"},
    ).json()["data"]
    sku = client.post(
        "/api/v1/skus",
        headers=auth_headers,
        json={
            "sku_code": f"SKU-M6-{uuid4().hex[:6]}",
            "name": "鉴权商品",
            "unit": "PCS",
        },
    ).json()["data"]
    return {"warehouse_id": wh["id"], "sku_id": sku["id"]}


def test_viewer_cannot_approve_inbound(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    created = client.post(
        "/api/v1/inbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "5.000"}],
        },
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/inbound-orders/{order_id}/submit", headers=auth_headers
        ).status_code
        == 200
    )

    viewer = _login(client, "viewer")
    denied = client.post(
        f"/api/v1/inbound-orders/{order_id}/approve", headers=viewer
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == 40300


def test_supervisor_approve_inbound_writes_operation_log(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    created = client.post(
        "/api/v1/inbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "3.000"}],
        },
    )
    order_id = created.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/inbound-orders/{order_id}/submit", headers=auth_headers
        ).status_code
        == 200
    )

    supervisor = _login(client, "supervisor")
    approved = client.post(
        f"/api/v1/inbound-orders/{order_id}/approve", headers=supervisor
    )
    assert approved.status_code == 200, approved.text

    logs = client.get(
        "/api/v1/operation-logs",
        headers=auth_headers,
        params={"action": "inbound.approve"},
    )
    assert logs.status_code == 200
    items = logs.json()["data"]["items"]
    assert any(
        item["action"] == "inbound.approve"
        and item["resource_id"] == str(order_id)
        and item["operator_name"] == "supervisor"
        for item in items
    )
    # 操作日志不含账变字段
    assert "change_qty" not in items[0]
    assert "qty_on_hand" not in items[0]


def test_login_writes_operation_log(client, auth_headers) -> None:
    _login(client, "operator")
    logs = client.get(
        "/api/v1/operation-logs",
        headers=auth_headers,
        params={"action": "auth.login"},
    )
    assert logs.status_code == 200
    assert any(item["operator_name"] == "operator" for item in logs.json()["data"]["items"])


def test_viewer_cannot_write_catalog(client) -> None:
    viewer = _login(client, "viewer")
    denied = client.post(
        "/api/v1/warehouses",
        headers=viewer,
        json={"warehouse_code": "WH-DENIED", "name": "拒绝仓"},
    )
    assert denied.status_code == 403


def test_operator_can_create_inbound_but_not_approve(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    operator = _login(client, "operator")
    created = client.post(
        "/api/v1/inbound-orders",
        headers=operator,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": "2.000"}],
        },
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/inbound-orders/{order_id}/submit", headers=operator
        ).status_code
        == 200
    )
    denied = client.post(
        f"/api/v1/inbound-orders/{order_id}/approve", headers=operator
    )
    assert denied.status_code == 403


def test_dictionaries_list_units(client, auth_headers) -> None:
    resp = client.get(
        "/api/v1/dictionaries",
        headers=auth_headers,
        params={"dict_type": "unit"},
    )
    assert resp.status_code == 200
    codes = {item["code"] for item in resp.json()["data"]["items"]}
    assert "PCS" in codes
    assert "BOX" in codes


def test_admin_can_assign_role(client, auth_headers) -> None:
    users = client.get("/api/v1/users", headers=auth_headers)
    assert users.status_code == 200
    viewer = next(u for u in users.json()["data"]["items"] if u["username"] == "viewer")
    # 赋回 viewer，验证接口可达
    patched = client.patch(
        f"/api/v1/users/{viewer['id']}/role",
        headers=auth_headers,
        json={"role_code": "viewer"},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["role_code"] == "viewer"


def test_viewer_cannot_read_operation_logs(client) -> None:
    viewer = _login(client, "viewer")
    denied = client.get("/api/v1/operation-logs", headers=viewer)
    assert denied.status_code == 403
