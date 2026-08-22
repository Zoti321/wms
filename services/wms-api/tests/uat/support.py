"""UAT 仅经 /api/v1 的助手：信封断言、角色登录、主数据与单据编排。"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx

SEED_PASSWORD = os.environ.get("UAT_PASSWORD", "Admin@123456")
ROLE_USERS = {
    "admin": os.environ.get("UAT_ADMIN_USERNAME", "admin"),
    "supervisor": os.environ.get("UAT_SUPERVISOR_USERNAME", "supervisor"),
    "operator": os.environ.get("UAT_OPERATOR_USERNAME", "operator"),
    "viewer": os.environ.get("UAT_VIEWER_USERNAME", "viewer"),
}

_ENVELOPE = ("code", "message", "data", "traceId")


def envelope(response) -> dict[str, Any]:
    body = response.json()
    missing = [key for key in _ENVELOPE if key not in body]
    assert not missing, f"响应缺少信封字段 {missing}: {body!r}"
    return body


def data_ok(response, *, status: int = 200) -> Any:
    body = envelope(response)
    assert response.status_code == status, response.text
    assert body["code"] == 0, response.text
    return body["data"]


def data_err(response, *, status: int, code: int | None = None) -> dict[str, Any]:
    body = envelope(response)
    assert response.status_code == status, response.text
    assert body["code"] != 0, response.text
    if code is not None:
        assert body["code"] == code, response.text
    return body


def qty(value: str) -> Decimal:
    return Decimal(value)


def non_negative(balance: dict[str, Any]) -> None:
    assert qty(balance["qty_on_hand"]) >= 0
    assert qty(balance["qty_frozen"]) >= 0
    assert qty(balance["qty_available"]) >= 0


def idem_headers(headers: dict[str, str], key: str | None = None) -> dict[str, str]:
    return {**headers, "Idempotency-Key": key or uuid4().hex}


def login(client, role: str) -> dict[str, str]:
    username = ROLE_USERS[role]
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": SEED_PASSWORD},
    )
    token = data_ok(response)["access_token"]
    assert isinstance(token, str) and token
    return {"Authorization": f"Bearer {token}"}


def unique_suffix() -> str:
    return uuid4().hex[:10]


def seed_masters(
    client,
    admin_headers: dict[str, str],
    *,
    safety_stock: str = "0.000",
    extra_location: bool = False,
) -> dict[str, Any]:
    suffix = unique_suffix()
    warehouse = data_ok(
        client.post(
            "/api/v1/warehouses",
            headers=admin_headers,
            json={"warehouse_code": f"WH-UAT-{suffix}", "name": f"验收仓-{suffix}"},
        )
    )
    sku = data_ok(
        client.post(
            "/api/v1/skus",
            headers=admin_headers,
            json={
                "sku_code": f"SKU-UAT-{suffix}",
                "name": f"验收商品-{suffix}",
                "unit": "PCS",
                "safety_stock": safety_stock,
            },
        )
    )
    location = data_ok(
        client.post(
            "/api/v1/locations",
            headers=admin_headers,
            json={
                "warehouse_id": warehouse["id"],
                "location_code": "A-01-01",
                "zone": "A",
                "aisle": "01",
                "bin": "01",
            },
        )
    )
    masters: dict[str, Any] = {
        "suffix": suffix,
        "warehouse_id": warehouse["id"],
        "sku_id": sku["id"],
        "location_id": location["id"],
        "warehouse": warehouse,
        "sku": sku,
        "location": location,
    }
    if extra_location:
        other = data_ok(
            client.post(
                "/api/v1/locations",
                headers=admin_headers,
                json={
                    "warehouse_id": warehouse["id"],
                    "location_code": "B-01-01",
                    "zone": "B",
                    "aisle": "01",
                    "bin": "01",
                },
            )
        )
        masters["location_b_id"] = other["id"]
    return masters


def create_inbound(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    return data_ok(
        client.post(
            "/api/v1/inbound-orders",
            headers=headers,
            json={
                "warehouse_id": masters["warehouse_id"],
                "order_type": "purchase",
                "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty_planned}],
            },
        )
    )


def submit_inbound(client, headers: dict[str, str], order_id: int) -> dict[str, Any]:
    return data_ok(client.post(f"/api/v1/inbound-orders/{order_id}/submit", headers=headers))


def approve_inbound(client, headers: dict[str, str], order_id: int) -> dict[str, Any]:
    return data_ok(client.post(f"/api/v1/inbound-orders/{order_id}/approve", headers=headers))


def putaway(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_put: str,
) -> dict[str, Any]:
    return data_ok(
        client.post(
            f"/api/v1/inbound-orders/{order_id}/putaway",
            headers=idem_headers(headers),
            json={"line_id": line_id, "location_id": location_id, "qty": qty_put},
        )
    )


def receive_purchase(
    client,
    tokens: dict[str, dict[str, str]],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    """仓管员建单提交，仓库主管审核，仓管员一次上架满行。"""
    order = create_inbound(client, tokens["operator"], masters, qty_planned)
    submit_inbound(client, tokens["operator"], order["id"])
    approved = approve_inbound(client, tokens["supervisor"], order["id"])
    line_id = approved["lines"][0]["id"]
    return putaway(
        client,
        tokens["operator"],
        approved["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put=qty_planned,
    )["order"]


def create_outbound(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    return data_ok(
        client.post(
            "/api/v1/outbound-orders",
            headers=headers,
            json={
                "warehouse_id": masters["warehouse_id"],
                "order_type": "sales",
                "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty_planned}],
            },
        )
    )


def submit_outbound(client, headers: dict[str, str], order_id: int) -> dict[str, Any]:
    return data_ok(client.post(f"/api/v1/outbound-orders/{order_id}/submit", headers=headers))


def pending_outbound(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    order = create_outbound(client, headers, masters, qty_planned)
    return submit_outbound(client, headers, order["id"])


def approve_outbound(
    client,
    headers: dict[str, str],
    order: dict[str, Any],
    location_id: int,
    *,
    key: str | None = None,
):
    return client.post(
        f"/api/v1/outbound-orders/{order['id']}/approve",
        headers=idem_headers(headers, key),
        json={
            "allocations": [
                {"line_id": order["lines"][0]["id"], "location_id": location_id}
            ]
        },
    )


def pick_outbound(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_pick: str,
) -> dict[str, Any]:
    return data_ok(
        client.post(
            f"/api/v1/outbound-orders/{order_id}/pick",
            headers=idem_headers(headers),
            json={"line_id": line_id, "location_id": location_id, "qty": qty_pick},
        )
    )


def list_balances(client, headers: dict[str, str], **params: Any) -> list[dict[str, Any]]:
    return data_ok(client.get("/api/v1/inventories", headers=headers, params=params))["items"]


def one_balance(client, headers: dict[str, str], masters: dict[str, Any]) -> dict[str, Any]:
    items = list_balances(
        client,
        headers,
        warehouse_id=masters["warehouse_id"],
        sku_id=masters["sku_id"],
    )
    assert len(items) == 1, items
    non_negative(items[0])
    return items[0]


def list_ledgers(client, headers: dict[str, str], **params: Any) -> list[dict[str, Any]]:
    return data_ok(
        client.get("/api/v1/inventories/ledgers", headers=headers, params=params)
    )["items"]


def list_alerts(client, headers: dict[str, str], warehouse_id: int) -> list[dict[str, Any]]:
    return data_ok(
        client.get(
            "/api/v1/inventories/alerts",
            headers=headers,
            params={"warehouse_id": warehouse_id},
        )
    )["items"]


def start_stocktake(
    client,
    headers: dict[str, str],
    warehouse_id: int,
    *,
    zone: str | None = "A",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"warehouse_id": warehouse_id}
    if zone is not None:
        payload["zone"] = zone
    return data_ok(
        client.post(
            "/api/v1/stocktakes",
            headers=idem_headers(headers),
            json=payload,
        )
    )["order"]


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
