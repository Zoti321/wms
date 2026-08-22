"""overview 端到端主路径：建仓/SKU/库位 → 入库上架 → 库存可见 → 出库分配 → 拣货实扣 → 流水按行可查。"""

from __future__ import annotations

from tests.uat.support import (
    approve_inbound,
    approve_outbound,
    create_inbound,
    data_ok,
    list_ledgers,
    one_balance,
    pending_outbound,
    pick_outbound,
    seed_masters,
    submit_inbound,
)


def test_端到端主路径_建仓入库上架库存可见出库分配拣货实扣流水可查(
    uat_client, tokens
) -> None:
    masters = seed_masters(uat_client, tokens["admin"])

    inbound = create_inbound(uat_client, tokens["operator"], masters, "10.000")
    submit_inbound(uat_client, tokens["operator"], inbound["id"])
    inbound_approved = approve_inbound(uat_client, tokens["supervisor"], inbound["id"])
    inbound_line_id = inbound_approved["lines"][0]["id"]
    put = data_ok(
        uat_client.post(
            f"/api/v1/inbound-orders/{inbound_approved['id']}/putaway",
            headers={
                **tokens["operator"],
                "Idempotency-Key": f"e2e-in-{masters['suffix']}",
            },
            json={
                "line_id": inbound_line_id,
                "location_id": masters["location_id"],
                "qty": "10.000",
            },
        )
    )
    assert put["order"]["status"] == "done"

    after_putaway = one_balance(uat_client, tokens["viewer"], masters)
    assert after_putaway["qty_on_hand"] == "10.000"
    assert after_putaway["qty_available"] == "10.000"

    outbound = pending_outbound(uat_client, tokens["operator"], masters, "10.000")
    allocated = data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], outbound, masters["location_id"]
        )
    )["order"]
    assert allocated["status"] == "approved"
    after_alloc = one_balance(uat_client, tokens["viewer"], masters)
    assert after_alloc["qty_frozen"] == "10.000"
    assert after_alloc["qty_available"] == "0.000"

    outbound_line_id = allocated["lines"][0]["id"]
    picked = pick_outbound(
        uat_client,
        tokens["operator"],
        allocated["id"],
        line_id=outbound_line_id,
        location_id=masters["location_id"],
        qty_pick="10.000",
    )
    assert picked["order"]["status"] == "done"
    after_pick = one_balance(uat_client, tokens["viewer"], masters)
    assert after_pick["qty_on_hand"] == "0.000"
    assert after_pick["qty_frozen"] == "0.000"

    inbound_ledgers = list_ledgers(
        uat_client, tokens["viewer"], ref_line_id=inbound_line_id
    )
    assert [row["ref_type"] for row in inbound_ledgers] == ["PUTAWAY"]
    outbound_ledgers = list_ledgers(
        uat_client, tokens["viewer"], ref_line_id=outbound_line_id
    )
    types = [row["ref_type"] for row in outbound_ledgers]
    assert "ALLOCATE" in types
    assert "PICK" in types
