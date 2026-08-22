"""平台验收：登录、最小权限、操作日志与库存流水分开查询。"""

from __future__ import annotations

from tests.uat.support import (
    create_inbound,
    data_err,
    data_ok,
    envelope,
    receive_purchase,
    seed_masters,
    submit_inbound,
)


def test_系统管理员_登录后获得可调用受保护接口的_access_token(uat_client, tokens) -> None:
    me = data_ok(uat_client.get("/api/v1/auth/me", headers=tokens["admin"]))
    assert me["username"] == "admin"
    assert me["role_code"] == "admin"

    warehouses = data_ok(uat_client.get("/api/v1/warehouses", headers=tokens["admin"]))
    assert "items" in warehouses


def test_无权限用户无法审核单据(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    order = create_inbound(uat_client, tokens["operator"], masters, "2.000")
    submit_inbound(uat_client, tokens["operator"], order["id"])

    denied_operator = uat_client.post(
        f"/api/v1/inbound-orders/{order['id']}/approve",
        headers=tokens["operator"],
    )
    data_err(denied_operator, status=403, code=40300)

    denied_viewer = uat_client.post(
        f"/api/v1/inbound-orders/{order['id']}/approve",
        headers=tokens["viewer"],
    )
    data_err(denied_viewer, status=403, code=40300)

    pending = data_ok(
        uat_client.get(
            f"/api/v1/inbound-orders/{order['id']}",
            headers=tokens["admin"],
        )
    )
    assert pending["status"] == "pending"


def test_系统管理员_可改用户角色且仓管员无权限改角色(uat_client, tokens) -> None:
    users = data_ok(uat_client.get("/api/v1/users", headers=tokens["admin"]))["items"]
    viewer = next(item for item in users if item["username"] == "viewer")
    patched = data_ok(
        uat_client.patch(
            f"/api/v1/users/{viewer['id']}/role",
            headers=tokens["admin"],
            json={"role_code": "viewer"},
        )
    )
    assert patched["role_code"] == "viewer"
    data_err(
        uat_client.patch(
            f"/api/v1/users/{viewer['id']}/role",
            headers=tokens["operator"],
            json={"role_code": "admin"},
        ),
        status=403,
        code=40300,
    )


def test_关键操作写入操作日志且可与库存流水分开查询(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    order = receive_purchase(uat_client, tokens, masters, "3.000")
    line_id = order["lines"][0]["id"]

    logs = data_ok(
        uat_client.get(
            "/api/v1/operation-logs",
            headers=tokens["admin"],
            params={"action": "inbound.approve"},
        )
    )["items"]
    assert any(
        item["action"] == "inbound.approve"
        and item["resource_id"] == str(order["id"])
        and item["operator_name"] == "supervisor"
        for item in logs
    )
    sample_log = next(item for item in logs if item["resource_id"] == str(order["id"]))
    assert "change_qty" not in sample_log
    assert "qty_on_hand" not in sample_log

    ledgers = data_ok(
        uat_client.get(
            "/api/v1/inventories/ledgers",
            headers=tokens["admin"],
            params={"ref_line_id": line_id},
        )
    )["items"]
    assert ledgers
    assert all(row["ref_type"] == "PUTAWAY" for row in ledgers)
    assert "operator_name" not in ledgers[0]
    assert "action" not in ledgers[0]
    assert "change_qty" in ledgers[0]


def test_JSON_写读接口使用统一响应信封(uat_client, tokens) -> None:
    body = envelope(uat_client.get("/api/v1/auth/me", headers=tokens["viewer"]))
    assert body["code"] == 0
    assert body["message"]
    assert body["traceId"]
