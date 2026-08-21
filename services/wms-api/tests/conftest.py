"""HTTP 集成测试夹具：真实 MySQL + Alembic 迁移。"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 默认与 .env.example 一致；隔离库可通过 TEST_DATABASE_URL 指定。
DEFAULT_TEST_URL = "mysql+pymysql://wms:wms@127.0.0.1:3306/wms?charset=utf8mb4"


def _database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL") or DEFAULT_TEST_URL


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "mysql: 需要可达的 MySQL")


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _database_url()
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except OperationalError as exc:
        pytest.skip(f"MySQL 不可用，跳过集成测试: {exc}")
    return url


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    os.environ["DATABASE_URL"] = database_url
    # 强制测试用 JWT，避免依赖本机 .env 密钥。
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod")
    os.environ.setdefault("APP_ENV", "test")

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
    return database_url


@pytest.fixture()
def client(migrated_database: str) -> Generator[TestClient, None, None]:
    # 延迟导入，确保环境变量已注入后再构建设置。
    from app.main import app
    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    reset_engine()
