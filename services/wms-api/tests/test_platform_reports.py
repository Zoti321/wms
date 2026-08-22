"""M7：基础报表 HTTP 主缝——JSON 日报与 CSV 导出。"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from uuid import uuid4

from tests.conftest import SEED_PASSWORD


def _login(client, username: str, password: str = SEED_PASSWORD) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_masters(client, auth_headers) -> dict[str, int]:
    suffix = uuid4().hex[:6]
    wh = client.post(
        "/api/v1/warehouses",
        headers=auth_headers,
        json={"warehouse_code": f"WH-RPT-{suffix}", "name": "报表仓"},
    ).json()["data"]
    sku = client.post(
        "/api/v1/skus",
        headers=auth_headers,
        json={
            "sku_code": f"SKU-RPT-{suffix}",
            "name": "报表商品",
            "unit": "PCS",
            "safety_stock": "100.000",
        },
    ).json()["data"]
    loc = client.post(
        "/api/v1/locations",
        headers=auth_headers,
        json={
            "warehouse_id": wh["id"],
            "location_code": "R-01-01",
            "zone": "R",
            "aisle": "01",
            "bin": "01",
        },
    ).json()["data"]
    return {"warehouse_id": wh["id"], "sku_id": sku["id"], "location_id": loc["id"]}


def _putaway(client, auth_headers, masters: dict[str, int], qty: str) -> None:
    created = client.post(
        "/api/v1/inbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "purchase",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty}],
        },
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["data"]["id"]
    assert (
        client.post(
            f"/api/v1/inbound-orders/{order_id}/submit", headers=auth_headers
        ).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/inbound-orders/{order_id}/approve", headers=auth_headers
    )
    assert approved.status_code == 200, approved.text
    line_id = approved.json()["data"]["lines"][0]["id"]
    put = client.post(
        f"/api/v1/inbound-orders/{order_id}/putaway",
        headers={**auth_headers, "Idempotency-Key": f"rpt-in-{uuid4().hex}"},
        json={
            "line_id": line_id,
            "location_id": masters["location_id"],
            "qty": qty,
        },
    )
    assert put.status_code == 200, put.text


def _pick(client, auth_headers, masters: dict[str, int], qty: str) -> None:
    created = client.post(
        "/api/v1/outbound-orders",
        headers=auth_headers,
        json={
            "warehouse_id": masters["warehouse_id"],
            "order_type": "sales",
            "lines": [{"sku_id": masters["sku_id"], "planned_qty": qty}],
        },
    )
    assert created.status_code == 200, created.text
    order = created.json()["data"]
    assert (
        client.post(
            f"/api/v1/outbound-orders/{order['id']}/submit", headers=auth_headers
        ).status_code
        == 200
    )
    approved = client.post(
        f"/api/v1/outbound-orders/{order['id']}/approve",
        headers={**auth_headers, "Idempotency-Key": f"rpt-ap-{uuid4().hex}"},
        json={
            "allocations": [
                {"line_id": order["lines"][0]["id"], "location_id": masters["location_id"]}
            ]
        },
    )
    assert approved.status_code == 200, approved.text
    order = approved.json()["data"]["order"]
    pick = client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers={**auth_headers, "Idempotency-Key": f"rpt-pk-{uuid4().hex}"},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": qty,
        },
    )
    assert pick.status_code == 200, pick.text


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def test_daily_report_requires_auth(client) -> None:
    resp = client.get(
        "/api/v1/reports/daily",
        params={"warehouse_id": 1, "business_date": "2026-08-22"},
    )
    assert resp.status_code == 401


def test_operator_cannot_read_daily_report(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    operator = _login(client, "operator")
    denied = client.get(
        "/api/v1/reports/daily",
        headers=operator,
        params={
            "warehouse_id": masters["warehouse_id"],
            "business_date": _today_utc(),
        },
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == 40300


def test_supervisor_daily_report_json_and_csv(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    _putaway(client, auth_headers, masters, "10.000")
    _pick(client, auth_headers, masters, "4.000")
    business_date = _today_utc()
    supervisor = _login(client, "supervisor")

    json_resp = client.get(
        "/api/v1/reports/daily",
        headers=supervisor,
        params={
            "warehouse_id": masters["warehouse_id"],
            "business_date": business_date,
        },
    )
    assert json_resp.status_code == 200, json_resp.text
    data = json_resp.json()["data"]
    assert data["warehouse_id"] == masters["warehouse_id"]
    assert data["business_date"] == business_date
    assert data["inbound_order_count"] == 1
    assert data["putaway_qty"] == "10.000"
    assert data["outbound_order_count"] == 1
    assert data["picked_qty"] == "4.000"
    assert data["sku_count"] == 1
    assert data["total_available"] == "6.000"
    assert data["open_alert_count"] >= 1

    csv_resp = client.get(
        "/api/v1/reports/daily.csv",
        headers=supervisor,
        params={
            "warehouse_id": masters["warehouse_id"],
            "business_date": business_date,
        },
    )
    assert csv_resp.status_code == 200, csv_resp.text
    assert "text/csv" in csv_resp.headers["content-type"]
    rows = list(csv.DictReader(io.StringIO(csv_resp.text)))
    assert len(rows) == 1
    row = rows[0]
    assert row["warehouse_id"] == str(masters["warehouse_id"])
    assert row["business_date"] == business_date
    assert row["inbound_order_count"] == "1"
    assert row["putaway_qty"] == "10.000"
    assert row["outbound_order_count"] == "1"
    assert row["picked_qty"] == "4.000"
    assert row["sku_count"] == "1"
    assert row["total_available"] == "6.000"
    assert int(row["open_alert_count"]) >= 1


def test_empty_business_day_returns_zero_summary(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    supervisor = _login(client, "supervisor")
    resp = client.get(
        "/api/v1/reports/daily",
        headers=supervisor,
        params={
            "warehouse_id": masters["warehouse_id"],
            "business_date": "2000-01-01",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["inbound_order_count"] == 0
    assert data["putaway_qty"] == "0.000"
    assert data["outbound_order_count"] == 0
    assert data["picked_qty"] == "0.000"
    assert data["sku_count"] == 0
    assert data["total_available"] == "0.000"
    assert data["open_alert_count"] == 0


def test_invalid_business_date_returns_400(client, auth_headers) -> None:
    masters = _seed_masters(client, auth_headers)
    supervisor = _login(client, "supervisor")
    resp = client.get(
        "/api/v1/reports/daily",
        headers=supervisor,
        params={
            "warehouse_id": masters["warehouse_id"],
            "business_date": "not-a-date",
        },
    )
    assert resp.status_code == 400


def test_missing_warehouse_returns_404(client, auth_headers) -> None:
    supervisor = _login(client, "supervisor")
    resp = client.get(
        "/api/v1/reports/daily",
        headers=supervisor,
        params={"warehouse_id": 999999999, "business_date": _today_utc()},
    )
    assert resp.status_code == 404
