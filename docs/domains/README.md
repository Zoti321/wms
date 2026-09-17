# 模块需求地图（WMS-SRS-001）

权威模块 SRS 在本目录的 **Markdown**。`docs/requirements.html` 仅供人浏览的索引（链到本目录）。

- **术语（glossary）**：[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md) 与各 [`src/*/CONTEXT.md`](../../src/inventory/CONTEXT.md) — 仅统一语言，不含验收标准
- **实现与表结构**：[`docs/dev/README.md`](../dev/README.md)
- **任务 spec**：GitHub Issues（`to-spec` 发布）

## 何时读哪个文件

| 任务涉及… | 先读 |
|---|---|
| 全局范围、角色、非功能、跨模块硬约束 | [overview.md](./overview.md) |
| 仓库 / SKU / 库位 / 供应商客户 | [catalog.md](./catalog.md) + [`src/catalog/CONTEXT.md`](../../src/catalog/CONTEXT.md) |
| 余额、流水、分配/实扣记账、预警 | [inventory.md](./inventory.md) + [`src/inventory/CONTEXT.md`](../../src/inventory/CONTEXT.md) |
| 入库单、上架 | [inbound.md](./inbound.md) + [`src/inbound/CONTEXT.md`](../../src/inbound/CONTEXT.md) |
| 出库单、分配、拣货、取消 | [outbound.md](./outbound.md) + [`src/outbound/CONTEXT.md`](../../src/outbound/CONTEXT.md) |
| 盘点、盘点锁、盈亏 | [stocktake.md](./stocktake.md) + [`src/stocktake/CONTEXT.md`](../../src/stocktake/CONTEXT.md) |
| 登录、角色权限、操作日志、字典 | [platform.md](./platform.md)（**非**限界上下文） |

接任务时：**只加载 overview（若涉及全局约束）+ 相关 1～2 个模块 SRS + 对应 `src/*/CONTEXT.md`**，不要默认通读全部。

## 模块列表

1. [overview.md](./overview.md) — 总览与全局规则
2. [catalog.md](./catalog.md) — 主数据
3. [inventory.md](./inventory.md) — 库存
4. [inbound.md](./inbound.md) — 入库
5. [outbound.md](./outbound.md) — 出库
6. [stocktake.md](./stocktake.md) — 盘点
7. [platform.md](./platform.md) — 平台（身份与审计）
