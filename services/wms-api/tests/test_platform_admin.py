"""平台管理扩展：用户创建/停用/改密、字典维护、/auth/me 权限码。"""

from __future__ import annotations

from uuid import uuid4

from app.platform.domain.permissions import ROLE_PERMISSIONS
from tests.conftest import SEED_PASSWORD
from tests.http_scenarios import data_ok, login


def _unique_username(prefix: str = "u") -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def test_me_returns_permissions_sorted(client, auth_headers) -> None:
    body = data_ok(client.get("/api/v1/auth/me", headers=auth_headers))
    expected = sorted(ROLE_PERMISSIONS["admin"])
    assert body["permissions"] == expected


def test_me_permissions_match_role_matrix(client) -> None:
    viewer = login(client, "viewer")
    body = data_ok(client.get("/api/v1/auth/me", headers=viewer))
    assert body["permissions"] == sorted(ROLE_PERMISSIONS["viewer"])


def test_operator_cannot_create_user(client) -> None:
    operator = login(client, "operator")
    denied = client.post(
        "/api/v1/users",
        headers=operator,
        json={
            "username": _unique_username(),
            "password": "Temp@123456",
            "role_code": "viewer",
        },
    )
    assert denied.status_code == 403


def test_admin_create_user_and_login(client, auth_headers) -> None:
    username = _unique_username("new")
    password = "NewUser@123456"
    created = data_ok(
        client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={
                "username": username,
                "password": password,
                "role_code": "operator",
            },
        )
    )
    assert created["username"] == username
    assert created["role_code"] == "operator"
    assert created["status"] == 1

    token = data_ok(
        client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
    )
    assert token["access_token"]

    logs = data_ok(
        client.get(
            "/api/v1/operation-logs",
            headers=auth_headers,
            params={"action": "user.create"},
        )
    )
    assert any(
        item["resource_id"] == str(created["id"]) for item in logs["items"]
    )


def test_create_user_duplicate_username_conflict(client, auth_headers) -> None:
    username = _unique_username("dup")
    payload = {
        "username": username,
        "password": "Temp@123456",
        "role_code": "viewer",
    }
    assert client.post("/api/v1/users", headers=auth_headers, json=payload).status_code == 200
    conflict = client.post("/api/v1/users", headers=auth_headers, json=payload)
    assert conflict.status_code == 409


def test_deactivate_user_blocks_login(client, auth_headers) -> None:
    username = _unique_username("off")
    password = "OffUser@123456"
    created = data_ok(
        client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={
                "username": username,
                "password": password,
                "role_code": "viewer",
            },
        )
    )
    deactivated = data_ok(
        client.post(
            f"/api/v1/users/{created['id']}/deactivate",
            headers=auth_headers,
        )
    )
    assert deactivated["status"] == 0

    denied = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert denied.status_code == 401


def test_cannot_deactivate_self(client, auth_headers) -> None:
    me = data_ok(client.get("/api/v1/auth/me", headers=auth_headers))
    blocked = client.post(
        f"/api/v1/users/{me['id']}/deactivate",
        headers=auth_headers,
    )
    assert blocked.status_code == 409


def test_cannot_deactivate_last_admin(client, auth_headers) -> None:
    users = data_ok(client.get("/api/v1/users", headers=auth_headers))["items"]
    admins = [u for u in users if u["role_code"] == "admin" and u["status"] == 1]
    assert len(admins) == 1
    blocked = client.post(
        f"/api/v1/users/{admins[0]['id']}/deactivate",
        headers=auth_headers,
    )
    assert blocked.status_code == 409


def test_reset_password_allows_new_login(client, auth_headers) -> None:
    username = _unique_username("rp")
    old_password = "OldPass@123456"
    new_password = "NewPass@123456"
    created = data_ok(
        client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={
                "username": username,
                "password": old_password,
                "role_code": "viewer",
            },
        )
    )
    data_ok(
        client.post(
            f"/api/v1/users/{created['id']}/reset-password",
            headers=auth_headers,
            json={"password": new_password},
        )
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": old_password},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": new_password},
        ).status_code
        == 200
    )


def test_viewer_cannot_write_dictionary(client) -> None:
    viewer = login(client, "viewer")
    denied = client.post(
        "/api/v1/dictionaries",
        headers=viewer,
        json={
            "dict_type": "unit",
            "code": "PAL",
            "name": "托",
            "sort_order": 9,
        },
    )
    assert denied.status_code == 403


def test_dictionary_crud_flow(client, auth_headers) -> None:
    code = f"X{uuid4().hex[:6].upper()}"
    created = data_ok(
        client.post(
            "/api/v1/dictionaries",
            headers=auth_headers,
            json={
                "dict_type": "unit",
                "code": code,
                "name": "测试单位",
                "sort_order": 99,
            },
        )
    )
    assert created["code"] == code
    assert created["name"] == "测试单位"

    updated = data_ok(
        client.patch(
            f"/api/v1/dictionaries/{created['id']}",
            headers=auth_headers,
            json={"name": "改后单位", "sort_order": 100},
        )
    )
    assert updated["name"] == "改后单位"
    assert updated["sort_order"] == 100

    listed = data_ok(
        client.get(
            "/api/v1/dictionaries",
            headers=auth_headers,
            params={"dict_type": "unit"},
        )
    )
    assert any(item["code"] == code for item in listed["items"])

    data_ok(
        client.post(
            f"/api/v1/dictionaries/{created['id']}/deactivate",
            headers=auth_headers,
        )
    )
    after = data_ok(
        client.get(
            "/api/v1/dictionaries",
            headers=auth_headers,
            params={"dict_type": "unit"},
        )
    )
    assert all(item["code"] != code for item in after["items"])
