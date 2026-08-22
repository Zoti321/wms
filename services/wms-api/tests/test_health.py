"""GET /health：进程与数据库可达性（issue #14）。"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


def test_health_returns_ok_when_database_reachable(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "checks": {"database": "ok"}}


def test_health_returns_degraded_when_database_unreachable(
    migrated_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad_url = "mysql+pymysql://wms:wms@127.0.0.1:59999/wms?charset=utf8mb4"
    monkeypatch.setenv("DATABASE_URL", bad_url)
    monkeypatch.setenv("HEALTH_CHECK_DB", "true")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-not-for-prod")
    monkeypatch.setenv("APP_ENV", "test")

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 503
        body = response.json()
        assert body == {"status": "degraded", "checks": {"database": "fail"}}

    get_settings.cache_clear()
    reset_engine()
    os.environ["DATABASE_URL"] = migrated_database
    get_settings.cache_clear()


def test_health_skips_database_check_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_url = "mysql+pymysql://wms:wms@127.0.0.1:59999/wms?charset=utf8mb4"
    monkeypatch.setenv("DATABASE_URL", bad_url)
    monkeypatch.setenv("HEALTH_CHECK_DB", "false")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-not-for-prod")
    monkeypatch.setenv("APP_ENV", "test")

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body == {"status": "ok", "checks": {"database": "skipped"}}

    get_settings.cache_clear()
    reset_engine()
