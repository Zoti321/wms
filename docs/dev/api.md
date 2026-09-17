# API 设计（节选）

统一前缀 `/api/v1`；鉴权 Header：`Authorization: Bearer <token>`；写接口建议带幂等键；响应包络：

```json
{
  "code": 0,
  "message": "ok",
  "data": { },
  "traceId": "..."
}
```

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 登录，返回 JWT |
| GET/POST | /warehouses | 仓库（MVP 只启用一个） |
| GET/POST | /skus | 商品列表 / 创建 |
| GET/POST | /locations | 库位管理 |
| POST | /inbound-orders | 创建入库单 |
| POST | /inbound-orders/{id}/approve | 审核入库单 |
| POST | /inbound-orders/{id}/putaway | 上架（部分）；增在库 |
| POST | /outbound-orders | 创建出库单 |
| POST | /outbound-orders/{id}/approve | 审核 = 分配（预留） |
| POST | /outbound-orders/{id}/pick | 拣货 = 预留实扣（部分） |
| POST | /outbound-orders/{id}/cancel | 取消未拣：释放预留 |
| GET | /inventories | 按仓库/SKU/库位查询 |
| GET | /inventories/ledgers | 库存流水 |
| GET | /inventories/alerts | 库存预警 |
| POST | /stocktakes | 创建盘点并加盘点锁 |
| POST | /stocktakes/{id}/approve | 审核盈亏、调账、释锁 |

完整契约见 `services/wms-api/` OpenAPI 与 [`services/wms-api/README.md`](../../services/wms-api/README.md)。
