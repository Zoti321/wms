"""盘点验收：审核前余额不变、审核后流水一致并释锁；锁期间上架与拣货均失败。"""

from __future__ import annotations

from uuid import uuid4

from tests.uat.support import (
    approve_inbound,
    approve_outbound,
    create_inbound,
    data_err,
    data_ok,
    idem_headers,
    list_ledgers,
    one_balance,
    pending_outbound,
    putaway,
    receive_purchase,
    seed_masters,
    start_stocktake,
    submit_inbound,
)


def test_仓库主管_发起盘点实盘审核后余额与流水一致并释锁(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "10.000")
    order = start_stocktake(
        uat_client, tokens["supervisor"], masters["warehouse_id"], zone="A"
    )
    assert order["status"] == "counting"
    assert len(order["lines"]) == 1
    assert order["lines"][0]["book_qty"] == "10.000"
    assert order["lines"][0]["counted_qty"] is None
    line_id = order["lines"][0]["id"]

    counted = data_ok(
        uat_client.post(
            f"/api/v1/stocktakes/{order['id']}/counts",
            headers=tokens["supervisor"],
            json={"lines": [{"line_id": line_id, "counted_qty": "12.000"}]},
        )
    )
    assert counted["lines"][0]["diff_qty"] == "2.000"
    assert one_balance(uat_client, tokens["viewer"], masters)["qty_on_hand"] == "10.000"

    approved = data_ok(
        uat_client.post(
            f"/api/v1/stocktakes/{order['id']}/approve",
            headers=idem_headers(tokens["supervisor"]),
        )
    )
    assert approved["order"]["status"] == "approved"
    assert one_balance(uat_client, tokens["viewer"], masters)["qty_on_hand"] == "12.000"

    ledgers = list_ledgers(
        uat_client,
        tokens["viewer"],
        ref_type="STOCKTAKE",
        ref_id=order["id"],
    )
    assert len(ledgers) == 1
    assert ledgers[0]["change_qty"] == "2.000"
    assert ledgers[0]["ref_line_id"] == line_id

    inbound = create_inbound(uat_client, tokens["operator"], masters, "1.000")
    submit_inbound(uat_client, tokens["operator"], inbound["id"])
    inbound_approved = approve_inbound(uat_client, tokens["supervisor"], inbound["id"])
    putaway(
        uat_client,
        tokens["operator"],
        inbound_approved["id"],
        line_id=inbound_approved["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_put="1.000",
    )
    assert one_balance(uat_client, tokens["viewer"], masters)["qty_on_hand"] == "13.000"


def test_仓库主管_盘点锁期间上架与拣货均失败释锁后可再上架(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "10.000")

    outbound = pending_outbound(uat_client, tokens["operator"], masters, "1.000")
    data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], outbound, masters["location_id"]
        )
    )

    stocktake = start_stocktake(
        uat_client, tokens["supervisor"], masters["warehouse_id"], zone="A"
    )

    inbound = create_inbound(uat_client, tokens["operator"], masters, "1.000")
    submit_inbound(uat_client, tokens["operator"], inbound["id"])
    inbound_approved = approve_inbound(uat_client, tokens["supervisor"], inbound["id"])
    putaway_denied = uat_client.post(
        f"/api/v1/inbound-orders/{inbound_approved['id']}/putaway",
        headers={**tokens["operator"], "Idempotency-Key": uuid4().hex},
        json={
            "line_id": inbound_approved["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    data_err(putaway_denied, status=409)

    pick_denied = uat_client.post(
        f"/api/v1/outbound-orders/{outbound['id']}/pick",
        headers={**tokens["operator"], "Idempotency-Key": uuid4().hex},
        json={
            "line_id": outbound["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    data_err(pick_denied, status=409)

    data_ok(
        uat_client.post(
            f"/api/v1/stocktakes/{stocktake['id']}/counts",
            headers=tokens["supervisor"],
            json={
                "lines": [
                    {
                        "line_id": stocktake["lines"][0]["id"],
                        "counted_qty": "10.000",
                    }
                ]
            },
        )
    )
    data_ok(
        uat_client.post(
            f"/api/v1/stocktakes/{stocktake['id']}/approve",
            headers=idem_headers(tokens["supervisor"]),
        )
    )

    putaway_ok = uat_client.post(
        f"/api/v1/inbound-orders/{inbound_approved['id']}/putaway",
        headers={**tokens["operator"], "Idempotency-Key": uuid4().hex},
        json={
            "line_id": inbound_approved["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    data_ok(putaway_ok)
    assert one_balance(uat_client, tokens["viewer"], masters)["qty_on_hand"] == "11.000"
