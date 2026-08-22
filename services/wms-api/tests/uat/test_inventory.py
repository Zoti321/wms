"""库存验收：上架后余额可见、流水按行与余额一致、安全库存预警开闭。"""

from __future__ import annotations

from tests.uat.support import (
    approve_outbound,
    data_ok,
    list_alerts,
    list_ledgers,
    one_balance,
    pending_outbound,
    receive_purchase,
    seed_masters,
)


def test_上架后库存查询可见余额(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    receive_purchase(uat_client, tokens, masters, "7.000")
    bal = one_balance(uat_client, tokens["viewer"], masters)
    assert bal["warehouse_id"] == masters["warehouse_id"]
    assert bal["sku_id"] == masters["sku_id"]
    assert bal["location_id"] == masters["location_id"]
    assert bal["qty_on_hand"] == "7.000"
    assert bal["qty_available"] == "7.000"
    assert bal["qty_frozen"] == "0.000"


def test_流水可按单据行查询且与余额变动一致(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"])
    order = receive_purchase(uat_client, tokens, masters, "8.000")
    line_id = order["lines"][0]["id"]
    ledgers = list_ledgers(uat_client, tokens["viewer"], ref_line_id=line_id)
    assert len(ledgers) == 1
    assert ledgers[0]["change_qty"] == "8.000"
    assert ledgers[0]["bal_qty"] == "8.000"
    assert ledgers[0]["ref_type"] == "PUTAWAY"
    assert one_balance(uat_client, tokens["viewer"], masters)["qty_on_hand"] == "8.000"


def test_可用量低于安全库存产生预警回升后解除(uat_client, tokens) -> None:
    masters = seed_masters(uat_client, tokens["admin"], safety_stock="10.000")
    receive_purchase(uat_client, tokens, masters, "12.000")
    assert list_alerts(uat_client, tokens["viewer"], masters["warehouse_id"]) == []

    pending = pending_outbound(uat_client, tokens["operator"], masters, "3.000")
    data_ok(
        approve_outbound(
            uat_client, tokens["supervisor"], pending, masters["location_id"]
        )
    )
    alerts = list_alerts(uat_client, tokens["viewer"], masters["warehouse_id"])
    assert len(alerts) == 1
    assert alerts[0]["sku_id"] == masters["sku_id"]
    assert alerts[0]["qty_available"] == "9.000"
    assert alerts[0]["safety_stock"] == "10.000"
    assert alerts[0]["status"] == "open"

    receive_purchase(uat_client, tokens, masters, "1.000")
    assert list_alerts(uat_client, tokens["viewer"], masters["warehouse_id"]) == []
    recovered = one_balance(uat_client, tokens["viewer"], masters)
    assert recovered["qty_available"] == "10.000"
    assert recovered["qty_on_hand"] == "13.000"
