"""出库验收：分配、部分拣货实扣、取消未拣、不足整单拒绝、并发不超卖、盘点锁拒拣。"""

from __future__ import annotations

from uuid import uuid4

from tests.uat.support import (
    approve_outbound,
    concurrent_posts,
    data_err,
    data_ok,
    idem_headers,
    list_ledgers,
    login,
    non_negative,
    one_balance,
    pending_outbound,
    pick_outbound,
    qty,
    receive_purchase,
    seed_masters,
    start_stocktake,
)


def test_仓库主管_出库审核完成分配后冻结增加可用下降(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "10.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "10.000")
    approved = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )
    order = approved["order"]
    assert order["status"] == "approved"
    assert order["lines"][0]["allocated_qty"] == "10.000"

    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_on_hand"] == "10.000"
    assert bal["qty_frozen"] == "10.000"
    assert bal["qty_available"] == "0.000"


def test_仓管员_按库位部分拣货后在库与冻结同减(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "10.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "10.000")
    order = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )["order"]
    picked = pick_outbound(
        uat_client,
        tokens["operator"],
        order["id"],
        line_id=order["lines"][0]["id"],
        location_id=masters["location_id"],
        qty_pick="4.000",
    )
    assert picked["order"]["status"] == "picking"
    assert picked["order"]["lines"][0]["picked_qty"] == "4.000"

    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_on_hand"] == "6.000"
    assert bal["qty_frozen"] == "6.000"
    assert bal["qty_available"] == "0.000"


def test_仓库主管_部分拣货后取消未拣正确释放预留且已实扣不抹(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "10.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "10.000")
    order = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )["order"]
    line_id = order["lines"][0]["id"]
    pick_outbound(
        uat_client,
        tokens["operator"],
        order["id"],
        line_id=line_id,
        location_id=masters["location_id"],
        qty_pick="4.000",
    )
    cancelled = data_ok(
        uat_client.post(
            f"/api/v1/outbound-orders/{order['id']}/cancel",
            headers=idem_headers(tokens["supervisor"]),
        )
    )
    assert cancelled["order"]["status"] == "done"
    assert cancelled["order"]["lines"][0]["picked_qty"] == "4.000"
    assert cancelled["order"]["lines"][0]["allocated_qty"] == "4.000"

    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_on_hand"] == "6.000"
    assert bal["qty_frozen"] == "0.000"
    assert bal["qty_available"] == "6.000"

    types = [row["ref_type"] for row in list_ledgers(uat_client, tokens["viewer"], ref_line_id=line_id)]
    assert "ALLOCATE" in types
    assert "PICK" in types
    assert "RELEASE" in types


def test_仓库主管_库存不足时整单审核被拒绝且无负可用负在库(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "3.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "5.000")
    denied = approve_outbound(
        uat_client, tokens["supervisor"], pending, masters["location_id"]
    )
    data_err(denied, status=400)

    detail = data_ok(
        uat_client.get(
            f"/api/v1/outbound-orders/{pending['id']}",
            headers=tokens["supervisor"],
        )
    )
    assert detail["status"] == "pending"
    assert detail["lines"][0]["allocated_qty"] == "0.000"

    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_frozen"] == "0.000"
    assert bal["qty_available"] == "3.000"
    non_negative(bal)


def test_两人几乎同时分配同一库存不超卖(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "5.000")
    first = pending_outbound(uat_client, tokens["operator"], masters, "5.000")
    second = pending_outbound(uat_client, tokens["operator"], masters, "5.000")
    supervisor_a = tokens["supervisor"]
    supervisor_b = login(uat_client, "supervisor")

    responses = concurrent_posts(
        uat_client,
        [
            {
                "path": f"/api/v1/outbound-orders/{first['id']}/approve",
                "headers": idem_headers(supervisor_a),
                "json": {
                    "allocations": [
                        {
                            "line_id": first["lines"][0]["id"],
                            "location_id": masters["location_id"],
                        }
                    ]
                },
            },
            {
                "path": f"/api/v1/outbound-orders/{second['id']}/approve",
                "headers": idem_headers(supervisor_b),
                "json": {
                    "allocations": [
                        {
                            "line_id": second["lines"][0]["id"],
                            "location_id": masters["location_id"],
                        }
                    ]
                },
            },
        ],
    )
    successes = [resp for resp in responses if resp.status_code == 200]
    failures = [resp for resp in responses if resp.status_code in (400, 409)]
    assert len(successes) == 1, [resp.text for resp in responses]
    assert len(failures) == 1

    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_on_hand"] == "5.000"
    assert bal["qty_frozen"] == "5.000"
    assert bal["qty_available"] == "0.000"
    non_negative(bal)
    assert qty(bal["qty_frozen"]) + qty(bal["qty_available"]) == qty(bal["qty_on_hand"])


def test_仓管员_盘点锁库位拣货被拒绝(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "2.000")
    pending = pending_outbound(uat_client, tokens["operator"], masters, "2.000")
    order = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )["order"]
    start_stocktake(uat_client, tokens["supervisor"], masters["warehouse_id"], zone="A")

    denied = uat_client.post(
        f"/api/v1/outbound-orders/{order['id']}/pick",
        headers={**tokens["operator"], "Idempotency-Key": uuid4().hex},
        json={
            "line_id": order["lines"][0]["id"],
            "location_id": masters["location_id"],
            "qty": "1.000",
        },
    )
    data_err(denied, status=409)
    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["qty_on_hand"] == "2.000"
    assert bal["qty_frozen"] == "2.000"
