"""M6：角色鉴权与操作日志 HTTP 外部缝。"""

from __future__ import annotations

from tests.http_scenarios import create_inbound, login, seed_masters, submit_inbound


def test_viewer_cannot_approve_inbound(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="M6", with_location=False)
    created = create_inbound(client, auth_headers, masters, "5.000")
    submit_inbound(client, auth_headers, created["id"])

    viewer = login(client, "viewer")
    denied = client.post(
        f"/api/v1/inbound-orders/{created['id']}/approve", headers=viewer
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == 40300


def test_supervisor_approve_inbound_writes_operation_log(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="M6", with_location=False)
    created = create_inbound(client, auth_headers, masters, "3.000")
    submit_inbound(client, auth_headers, created["id"])

    supervisor = login(client, "supervisor")
    approved = client.post(
        f"/api/v1/inbound-orders/{created['id']}/approve", headers=supervisor
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
        and item["resource_id"] == str(created["id"])
        and item["operator_name"] == "supervisor"
        for item in items
    )
    assert "change_qty" not in items[0]
    assert "qty_on_hand" not in items[0]


def test_login_writes_operation_log(client, auth_headers) -> None:
    login(client, "operator")
    logs = client.get(
        "/api/v1/operation-logs",
        headers=auth_headers,
        params={"action": "auth.login"},
    )
    assert logs.status_code == 200
    assert any(item["operator_name"] == "operator" for item in logs.json()["data"]["items"])


def test_viewer_cannot_write_catalog(client) -> None:
    viewer = login(client, "viewer")
    denied = client.post(
        "/api/v1/warehouses",
        headers=viewer,
        json={"warehouse_code": "WH-DENIED", "name": "拒绝仓"},
    )
    assert denied.status_code == 403


def test_operator_can_create_inbound_but_not_approve(client, auth_headers) -> None:
    masters = seed_masters(client, auth_headers, prefix="M6", with_location=False)
    operator = login(client, "operator")
    created = create_inbound(client, operator, masters, "2.000")
    submit_inbound(client, operator, created["id"])
    denied = client.post(
        f"/api/v1/inbound-orders/{created['id']}/approve", headers=operator
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
    patched = client.patch(
        f"/api/v1/users/{viewer['id']}/role",
        headers=auth_headers,
        json={"role_code": "viewer"},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["role_code"] == "viewer"


def test_viewer_cannot_read_operation_logs(client) -> None:
    viewer = login(client, "viewer")
    denied = client.get("/api/v1/operation-logs", headers=viewer)
    assert denied.status_code == 403
