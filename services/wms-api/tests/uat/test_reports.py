"""基础报表验收：主路径动作后可拉日报 JSON/CSV（需 report:read）。"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from tests.uat.support import (
    approve_outbound,
    data_err,
    data_ok,
    pending_outbound,
    pick_outbound,
    receive_purchase,
    seed_masters,
)


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def test_报表读者_主路径后可拉取日报JSON与CSV(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"], safety_stock="100.000")
    receive_purchase(uat_client, tokens, masters, "10.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "4.000")
    order = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )["order"]
    pick_outbound(
        uat_client,
        tokens["operator"],
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_pick="4.000",
    )
    business_date = _today_utc()

    denied = uat_client.get(
        "/api/v1/reports/daily",
        headers=tokens["operator"],
        params={"warehouse_id": masters["warehouse_id"], "business_date": business_date},
    )
    data_err(denied, status=403, code=40300)

    payload = data_ok(
        uat_client.get(
            "/api/v1/reports/daily",
            headers=tokens["supervisor"],
            params={
                "warehouse_id": masters["warehouse_id"],
                "business_date": business_date,
            },
        )
    )
    assert payload["warehouse_id"] == masters["warehouse_id"]
    assert payload["business_date"] == business_date
    assert payload["inbound_order_count"] == 1
    assert payload["putaway_qty"] == "10.000"
    assert payload["outbound_order_count"] == 1
    assert payload["picked_qty"] == "4.000"
    assert payload["sku_count"] == 1
    assert payload["total_available"] == "6.000"
    assert payload["open_alert_count"] >= 1

    csv_resp = uat_client.get(
        "/api/v1/reports/daily.csv",
        headers=tokens["supervisor"],
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
    assert row["inbound_order_count"] == "1"
    assert row["putaway_qty"] == "10.000"
    assert row["picked_qty"] == "4.000"
    assert row["total_available"] == "6.000"
