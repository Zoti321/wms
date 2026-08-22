"""GET /metrics：Prometheus 运行监控（issue #15）。"""

from __future__ import annotations

import os
import re

import pytest
from fastapi.testclient import TestClient

from tests.http_scenarios import (
    approve_outbound,
    login,
    pending_outbound,
    seed_masters,
)


def _metrics_app(monkeypatch: pytest.MonkeyPatch, *, enabled: bool) -> TestClient:
    monkeypatch.setenv("METRICS_ENABLED", "true" if enabled else "false")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-not-for-prod")
    monkeypatch.setenv("APP_ENV", "dev")

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    return TestClient(create_app())


def _scrape(client: TestClient) -> str:
    response = client.get("/metrics")
    assert response.status_code == 200, response.text
    assert "text/plain" in response.headers.get("content-type", "")
    return response.text


def test_metrics_disabled_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    with _metrics_app(monkeypatch, enabled=False) as client:
        assert client.get("/metrics").status_code == 404


def test_metrics_disabled_by_default_in_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("METRICS_ENABLED", raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-not-for-prod")

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app()) as client:
        assert client.get("/metrics").status_code == 404

    get_settings.cache_clear()
    reset_engine()


def test_metrics_enabled_exposes_http_and_pool_gauges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _metrics_app(monkeypatch, enabled=True) as client:
        body = _scrape(client)
        assert "http_requests_total" in body
        assert "wms_db_pool_size" in body
        assert "wms_db_pool_checked_out" in body


def test_allocate_insufficient_increments_inventory_counter(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    migrated_database: str,
) -> None:
    """库存不足审核分配 → wms_inventory_operation_total insufficient 递增。"""
    os.environ["METRICS_ENABLED"] = "true"
    os.environ["DATABASE_URL"] = migrated_database
    os.environ["APP_ENV"] = "dev"

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app()) as metrics_client:
        before = _scrape(metrics_client)
        before_count = _counter_value(
            before,
            operation="allocate",
            result="insufficient",
        )

        masters = seed_masters(
            metrics_client, auth_headers, prefix="MET", location_code="C-01-01", zone="C"
        )
        pending = pending_outbound(metrics_client, auth_headers, masters, "5.000")
        supervisor = login(metrics_client, "supervisor")
        response = approve_outbound(
            metrics_client, supervisor, pending, masters["location_id"]
        )
        assert response.status_code == 400, response.text

        after = _scrape(metrics_client)
        after_count = _counter_value(
            after,
            operation="allocate",
            result="insufficient",
        )
        assert after_count == before_count + 1

    os.environ.pop("METRICS_ENABLED", None)
    get_settings.cache_clear()
    reset_engine()


def _counter_value(body: str, *, operation: str, result: str) -> float:
    pattern = (
        rf'^wms_inventory_operation_total{{operation="{operation}",result="{result}"}} (\d+(?:\.\d+)?)$'
    )
    match = re.search(pattern, body, re.MULTILINE)
    return float(match.group(1)) if match else 0.0
