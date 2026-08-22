"""UAT 薄层：角色登录、并发 POST；编排复用 tests.http_scenarios。"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from tests.http_scenarios import (
    approve_inbound,
    approve_outbound,
    create_inbound,
    create_outbound,
    data_err,
    data_ok,
    envelope,
    idem_headers,
    list_alerts,
    list_balances,
    list_ledgers,
    non_negative,
    one_balance,
    pending_outbound,
    pick_outbound_ok,
    putaway_ok,
    qty,
    receive_purchase as _receive_purchase,
    seed_masters,
    start_stocktake,
    submit_inbound,
    submit_outbound,
    unique_suffix,
)

SEED_PASSWORD = os.environ.get("UAT_PASSWORD", "Admin@123456")
ROLE_USERS = {
    "admin": os.environ.get("UAT_ADMIN_USERNAME", "admin"),
    "supervisor": os.environ.get("UAT_SUPERVISOR_USERNAME", "supervisor"),
    "operator": os.environ.get("UAT_OPERATOR_USERNAME", "operator"),
    "viewer": os.environ.get("UAT_VIEWER_USERNAME", "viewer"),
}

__all__ = [
    "ROLE_USERS",
    "SEED_PASSWORD",
    "approve_inbound",
    "approve_outbound",
    "concurrent_posts",
    "create_inbound",
    "create_outbound",
    "data_err",
    "data_ok",
    "envelope",
    "idem_headers",
    "list_alerts",
    "list_balances",
    "list_ledgers",
    "login",
    "non_negative",
    "one_balance",
    "pending_outbound",
    "pick_outbound",
    "putaway",
    "qty",
    "receive_purchase",
    "seed_masters",
    "start_stocktake",
    "submit_inbound",
    "submit_outbound",
    "unique_suffix",
]


def login(client, role: str) -> dict[str, str]:
    from tests.http_scenarios import login as _login

    return _login(client, ROLE_USERS[role], password=SEED_PASSWORD)


def receive_purchase(
    client,
    tokens: dict[str, dict[str, str]],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    return _receive_purchase(
        client,
        tokens["operator"],
        tokens["supervisor"],
        masters,
        qty_planned,
    )


def putaway(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_put: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    return putaway_ok(
        client,
        headers,
        order_id,
        line_id=line_id,
        location_id=location_id,
        qty_put=qty_put,
        idempotency_key=idempotency_key,
    )


def pick_outbound(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_pick: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    return pick_outbound_ok(
        client,
        headers,
        order_id,
        line_id=line_id,
        location_id=location_id,
        qty_pick=qty_pick,
        idempotency_key=idempotency_key,
    )


def concurrent_posts(client, specs: list[dict[str, Any]]) -> list[Any]:
    """几乎同时发出多条 POST。本地走 ASGI 并发；UAT_BASE_URL 走线程 HTTP。"""
    if os.environ.get("UAT_BASE_URL", "").strip():
        with ThreadPoolExecutor(max_workers=len(specs)) as pool:
            futures = [
                pool.submit(
                    client.post,
                    spec["path"],
                    headers=spec["headers"],
                    json=spec.get("json"),
                )
                for spec in specs
            ]
            return [future.result() for future in futures]

    app = client.app

    async def _race() -> list[httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://uat.local"
        ) as async_client:
            return list(
                await asyncio.gather(
                    *[
                        async_client.post(
                            spec["path"],
                            headers=spec["headers"],
                            json=spec.get("json"),
                        )
                        for spec in specs
                    ]
                )
            )

    return asyncio.run(_race())
