# 单据状态机

## 入库

`DRAFT` → `PENDING` → `APPROVED` → `PUTAWAY` → `DONE`

未上架可转 `CANCELLED`。已上架数量不可靠取消抹掉；纠错走调整或二期冲销。

## 出库

`DRAFT` → `PENDING` → `APPROVED` → `PICKING` → `DONE`

`APPROVED` 时已完成分配。取消：释放未拣预留；若已有实扣，已出库部分保留，未拣关闭或整单按规则终结。已实扣纠错 → 退货入库。
