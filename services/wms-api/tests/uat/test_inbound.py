"""入库验收：部分上架、盘点锁拒上架、未上架可取消且已上架取消不抹账。"""

from __future__ import annotations

from uuid import uuid4

from tests.uat.support import (
    approve_inbound,
    create_inbound,
    data_err,
    data_ok,
    list_balances,
    list_ledgers,
    putaway,
    seed_masters,
    start_stocktake,
    submit_inbound,
)


def test_仓管员_采购入库多次部分上架后行累计流水与在库一致(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    order = create_inbound(uat_client, tokens["operator"], masters, "10.000")
    submit_inbound(uat_client, tokens["operator"], order["id"])
    approved = approve_inbound(uat_client, tokens["supervisor"], order["id"])
    line_id = approved["lines"][0]["id"]

    first = putaway(
        uat_client,
        tokens["operator"],
        approved["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put="4.000",
    )
    assert first["order"]["status"] == "putaway"
    assert first["order"]["lines"][0]["putaway_qty"] == "4.000"

    second = putaway(
        uat_client,
        tokens["operator"],
        approved["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_put="6.000",
    )
    assert second["order"]["status"] == "done"
    assert second["order"]["lines"][0]["putaway_qty"] == "10.000"

    items = list_balances(
        uat_client,
        tokens["viewer"],
        warehouse_id=masters["warehouse_id"],
        sku_id=masters["sku_id"],
    )
    assert items[0]["qty_on_hand"] == "10.000"
    assert items[0]["qty_available"] == "10.000"
    assert items[0]["qty_frozen"] == "0.000"

    ledgers = list_ledgers(uat_client, tokens["viewer"], ref_line_id=line_id)
    assert len(ledgers) == 2
    assert {row["change_qty"] for row in ledgers} == {"4.000", "6.000"}
    assert all(row["ref_type"] == "PUTAWAY" for row in ledgers)


def test_仓管员_盘点锁库位上架被拒绝(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    order = create_inbound(uat_client, tokens["operator"], masters, "2.000")
    submit_inbound(uat_client, tokens["operator"], order["id"])
    approved = approve_inbound(uat_client, tokens["supervisor"], order["id"])
    start_stocktake(
        uat_client, tokens["supervisor"], masters["warehouse_id"], zone="A"
    )

    denied = uat_client.post(
        f"/api/v1/inbound-orders/{approved['id']}/putaway",
        headers={**tokens["operator"], "Idempotency-Key": uuid4().hex},
        json={
            "line_id": approved["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    data_err(denied, status=409)
    assert list_balances(
        uat_client, tokens["viewer"], warehouse_id=masters["warehouse_id"]
    ) == []


def test_仓管员_未上架可取消_已上架取消不抹账(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    draft = create_inbound(uat_client, tokens["operator"], masters, "3.000")
    submit_inbound(uat_client, tokens["operator"], draft["id"])
    approve_inbound(uat_client, tokens["supervisor"], draft["id"])
    cancelled = data_ok(
        uat_client.post(
            f"/api/v1/inbound-orders/{draft['id']}/cancel",
            headers=tokens["operator"],
        )
    )
    assert cancelled["status"] == "cancelled"

    order = create_inbound(uat_client, tokens["operator"], masters, "3.000")
    submit_inbound(uat_client, tokens["operator"], order["id"])
    approved = approve_inbound(uat_client, tokens["supervisor"], order["id"])
    putaway(
        uat_client,
        tokens["operator"],
        approved["id"],
        line_id=approved["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="1.000",
    )
    blocked = uat_client.post(
        f"/api/v1/inbound-orders/{approved['id']}/cancel",
        headers=tokens["operator"],
    )
    data_err(blocked, status=409)

    items = list_balances(
        uat_client,
        tokens["viewer"],
        warehouse_id=masters["warehouse_id"],
        sku_id=masters["sku_id"],
    )
    assert items[0]["qty_on_hand"] == "1.000"
    still = data_ok(
        uat_client.get(
            f"/api/v1/inbound-orders/{approved['id']}",
            headers=tokens["operator"],
        )
    )
    assert still["lines"][0]["putaway_qty"] == "1.000"
    assert still["status"] != "cancelled"
