"""HTTP 测试编排 deep module：信封断言、主数据种子、入出库/盘点剧本（/api/v1）。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

from tests.conftest import SEED_PASSWORD

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


def unique_suffix() -> str:
    return uuid4().hex[:10]


def login(client, username: str, password: str = SEED_PASSWORD) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = data_ok(response)["access_token"]
    assert isinstance(token, str) and token
    return {"Authorization": f"Bearer {token}"}


def seed_masters(
    client,
    headers: dict[str, str],
    *,
    prefix: str = "HTTP",
    safety_stock: str = "0.000",
    extra_location: bool = False,
    with_location: bool = True,
    location_code: str = "A-01-01",
    zone: str = "A",
    second_location_code: str = "B-01-01",
    second_zone: str = "B",
) -> dict[str, Any]:
    suffix = unique_suffix()
    code_tag = f"{prefix}-{suffix}"
    warehouse = data_ok(
        client.post(
            "/api/v1/warehouses",
            headers=headers,
            json={"warehouse_code": f"WH-{code_tag}", "name": f"测试仓-{code_tag}"},
        )
    )
    sku = data_ok(
        client.post(
            "/api/v1/skus",
            headers=headers,
            json={
                "sku_code": f"SKU-{code_tag}",
                "name": f"测试商品-{code_tag}",
                "unit": "PCS",
                "safety_stock": safety_stock,
            },
        )
    )
    masters: dict[str, Any] = {
        "suffix": suffix,
        "prefix": prefix,
        "warehouse_id": warehouse["id"],
        "sku_id": sku["id"],
        "warehouse": warehouse,
        "sku": sku,
    }
    if with_location:
        location = data_ok(
            client.post(
                "/api/v1/locations",
                headers=headers,
                json={
                    "warehouse_id": warehouse["id"],
                    "location_code": location_code,
                    "zone": zone,
                    "aisle": "01",
                    "bin": "01",
                },
            )
        )
        masters["location_id"] = location["id"]
        masters["location"] = location
    if extra_location:
        other = data_ok(
            client.post(
                "/api/v1/locations",
                headers=headers,
                json={
                    "warehouse_id": warehouse["id"],
                    "location_code": second_location_code,
                    "zone": second_zone,
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


def approved_inbound(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str = "10.000",
) -> dict[str, Any]:
    """建单 → 提交 → 审核，返回审核后单据。"""
    order = create_inbound(client, headers, masters, qty_planned)
    submit_inbound(client, headers, order["id"])
    return approve_inbound(client, headers, order["id"])


def putaway(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_put: str,
    idempotency_key: str | None = None,
):
    return client.post(
        f"/api/v1/inbound-orders/{order_id}/putaway",
        headers=idem_headers(headers, idempotency_key),
        json={"line_id": line_id, "location_id": location_id, "qty": qty_put},
    )


def putaway_ok(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_put: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    return data_ok(
        putaway(
            client,
            headers,
            order_id,
            line_id=line_id,
            location_id=location_id,
            qty_put=qty_put,
            idempotency_key=idempotency_key,
        )
    )


def receive_purchase(
    client,
    operator_headers: dict[str, str],
    supervisor_headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str,
) -> dict[str, Any]:
    """仓管员建单提交，仓库主管审核，仓管员一次上架满行。"""
    order = create_inbound(client, operator_headers, masters, qty_planned)
    submit_inbound(client, operator_headers, order["id"])
    approved = approve_inbound(client, supervisor_headers, order["id"])
    line_id = approved["lines"][0]["id"]
    return putaway_ok(
        client,
        operator_headers,
        approved["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put=qty_planned,
    )["order"]


def putaway_stock(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str = "10.000",
) -> None:
    """单角色完成采购入库上架（集成测常用）。"""
    approved = approved_inbound(client, headers, masters, qty_planned)
    putaway_ok(
        client,
        headers,
        approved["id"],
        line_id=approved["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put=qty_planned,
    )


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
    idempotency_key: str | None = None,
):
    return client.post(
        f"/api/v1/outbound-orders/{order_id}/pick",
        headers=idem_headers(headers, idempotency_key),
        json={"line_id": line_id, "location_id": location_id, "qty": qty_pick},
    )


def pick_outbound_ok(
    client,
    headers: dict[str, str],
    order_id: int,
    *,
    line_id: int,
    location_id: int,
    qty_pick: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    return data_ok(
        pick_outbound(
            client,
            headers,
            order_id,
            line_id=line_id,
            location_id=location_id,
            qty_pick=qty_pick,
            idempotency_key=idempotency_key,
        )
    )


def fulfill_outbound_pick(
    client,
    headers: dict[str, str],
    masters: dict[str, Any],
    qty_planned: str,
) -> None:
    """建单 → 提交 → 分配 → 实扣满行。"""
    pending = pending_outbound(client, headers, masters, qty_planned)
    approved = approve_outbound(client, headers, pending, masters["location_id"])
    assert approved.status_code == 200, approved.text
    order = approved.json()["data"]["order"]
    pick_outbound_ok(
        client,
        headers,
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_pick=qty_planned,
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
