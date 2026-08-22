"""UAT 夹具：本地 ASGI TestClient，或 UAT_BASE_URL 指向 staging。"""

from __future__ import annotations

import os
from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.uat.support import login


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    marker = pytest.mark.uat
    for item in items:
        item.add_marker(marker)


@pytest.fixture(scope="session")
def uat_client(request: pytest.FixtureRequest) -> Generator[object, None, None]:
    base = os.environ.get("UAT_BASE_URL", "").strip().rstrip("/")
    if base:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            yield client
        return

    request.getfixturevalue("migrated_database")
    from app.inventory.application.lock import reset_location_lock_checker
    from app.main import app
    from app.shared.config import get_settings
    from app.shared.db import reset_engine

    get_settings.cache_clear()
    reset_engine()
    reset_location_lock_checker()
    with TestClient(app) as client:
        yield client
    reset_location_lock_checker()
    get_settings.cache_clear()
    reset_engine()


@pytest.fixture(scope="session")
def tokens(uat_client) -> dict[str, dict[str, str]]:
    return {
        "admin": login(uat_client, "admin"),
        "supervisor": login(uat_client, "supervisor"),
        "operator": login(uat_client, "operator"),
        "viewer": login(uat_client, "viewer"),
    }
