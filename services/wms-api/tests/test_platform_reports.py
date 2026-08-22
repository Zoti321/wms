"""M7：基础报表 HTTP 主缝——JSON 日报与 CSV 导出。"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from tests.http_scenarios import fulfill_outbound_pick, login, putaway_stock, seed_masters


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def test_daily_report_requires_auth(client) -> None:
    resp = client.get(
        "/api/v1/reports/daily",
        params={"warehouse_id": 1, "business_date": "2026-08-22"},
    )
    assert resp.status_code == 401


def test_operator_cannot_read_daily_report(client, auth_headers) -> None:
    masters = seed_masters(
        client,
        auth_headers,
        prefix="RPT",
        safety_stock="100.000",
        location_code="R-01-01",
        zone="R",
    )
    operator = login(client, "operator")
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
    masters = seed_masters(
        client,
        auth_headers,
        prefix="RPT",
        safety_stock="100.000",
        location_code="R-01-01",
        zone="R",
    )
    putaway_stock(client, auth_headers, masters, "10.000")
    fulfill_outbound_pick(client, auth_headers, masters, "4.000")
    business_date = _today_utc()
    supervisor = login(client, "supervisor")

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
    masters = seed_masters(
        client,
        auth_headers,
        prefix="RPT",
        safety_stock="100.000",
        location_code="R-01-01",
        zone="R",
    )
    supervisor = login(client, "supervisor")
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
    masters = seed_masters(
        client,
        auth_headers,
        prefix="RPT",
        safety_stock="100.000",
        location_code="R-01-01",
        zone="R",
    )
    supervisor = login(client, "supervisor")
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
    supervisor = login(client, "supervisor")
    resp = client.get(
        "/api/v1/reports/daily",
        headers=supervisor,
        params={"warehouse_id": 999999999, "business_date": _today_utc()},
    )
    assert resp.status_code == 404
