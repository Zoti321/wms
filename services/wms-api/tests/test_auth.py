"""M0 登录与鉴权 HTTP 行为（外部缝）。"""

from __future__ import annotations

from tests.conftest import SEED_PASSWORD, SEED_USERNAME


def test_health_does_not_require_auth(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_rejects_wrong_password(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": SEED_USERNAME, "password": "wrong-password"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["code"] != 0
    assert "data" in body


def test_login_returns_access_token_for_seed_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": SEED_USERNAME, "password": SEED_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert body["data"]["token_type"] == "bearer"
    assert isinstance(body["data"]["access_token"], str)
    assert body["data"]["access_token"]
    assert "traceId" in body


def test_protected_route_rejects_missing_token(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_route_rejects_invalid_token(client) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": SEED_USERNAME, "password": SEED_PASSWORD},
    )
    token = login.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == SEED_USERNAME
    assert body["data"]["role_code"] == "admin"
