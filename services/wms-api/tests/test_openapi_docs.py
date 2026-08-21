"""OpenAPI 交互文档：非 prod 可访问；生产关闭。"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


def test_openapi_docs_available_in_non_production(client) -> None:
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower() or "openapi" in docs.text.lower()

    redoc = client.get("/redoc")
    assert redoc.status_code == 200

    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    body = spec.json()
    assert body["info"]["title"] == "仓脉 WMS API"
    assert "description" in body["info"]
    assert "Authorize" in body["info"]["description"] or "Bearer" in body["info"]["description"]
    tag_names = {tag["name"] for tag in body.get("tags", [])}
    assert {"auth", "catalog", "inventory", "inbound", "outbound"}.issubset(tag_names)
    # 受保护路由已挂 Bearer，可在 Swagger 中 Authorize 后试调
    me = body["paths"]["/api/v1/auth/me"]["get"]
    assert me.get("security")


@pytest.mark.parametrize("prod_env", ["production", "prod"])
def test_openapi_docs_disabled_in_production(
    migrated_database: str, monkeypatch: pytest.MonkeyPatch, prod_env: str
) -> None:
    monkeypatch.setenv("APP_ENV", prod_env)
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-not-for-prod")

    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    application = create_app()
    assert application.docs_url is None
    assert application.redoc_url is None
    assert application.openapi_url is None

    with TestClient(application) as test_client:
        assert test_client.get("/docs").status_code == 404
        assert test_client.get("/redoc").status_code == 404
        assert test_client.get("/openapi.json").status_code == 404
        assert test_client.get("/health").status_code == 200

    get_settings.cache_clear()
    reset_engine()
    # 避免污染后续用例的 APP_ENV
    os.environ["APP_ENV"] = "test"
    get_settings.cache_clear()
