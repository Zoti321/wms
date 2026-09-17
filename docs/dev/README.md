# 开发设计说明书（WMS-SDD-001）

文档编号 WMS-SDD-001 · 版本 1.4 · 2026-08-24

实现路径：技术栈、限界上下文落码、数据模型、API、状态机与里程碑。

- **业务规则**：[`docs/domains/README.md`](../domains/README.md)（模块化 SRS）
- **术语**：[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md) 与各 [`src/*/CONTEXT.md`](../../src/inventory/CONTEXT.md)
- **架构决策**：[`docs/adr/`](../adr/)

## 设计原则

1. **库存唯一账本**：只有 inventory 上下文改数量并写 ledger；inbound / outbound / stocktake 发请求，以记账成功为准。
2. **出库软分配**：审核 = 可用→冻结；拣货 = 预留实扣；取消未拣 = 释放预留。
3. **盘点锁**：锁库位作业，不靠把数量记入冻结数量实现。
4. **幂等与防超卖**：分配/实扣使用库存行 `version` 乐观锁；重复提交用业务单号 + 执行幂等键（MVP 幂等记录存 MySQL，不上 Redis）。
5. **仓库一等**：表与 API 均带 `warehouse_id`；MVP 只启用一个仓库。
6. **交付面 ≠ 上下文**：后端、网页后台、小程序是适配器；领域按 catalog / inventory / inbound / outbound / stocktake 分包。

## 目录

| 文档 | 内容 |
|------|------|
| [stack.md](./stack.md) | 技术选型 |
| [architecture.md](./architecture.md) | 系统架构与模块划分 |
| [data-model.md](./data-model.md) | 核心数据模型 |
| [api.md](./api.md) | API 设计（节选） |
| [state-machines.md](./state-machines.md) | 入出库状态机 |
| [repo-layout.md](./repo-layout.md) | Monorepo 工程结构 |
| [conventions.md](./conventions.md) | 开发规范 |
| [milestones.md](./milestones.md) | 里程碑计划 |
| [ops.md](./ops.md) | 部署与运维要点 |
| [backend-status.md](./backend-status.md) | 后端实现状态与缺口（**活文档**） |
| [warehouse-comparison.md](./warehouse-comparison.md) | 与参考项目 yeqifu/warehouse 的功能对比与缺口 |
| [mini-program-summary.md](./mini-program-summary.md) | 小程序作业端摘要 |

人类浏览入口：[`docs/development.html`](../development.html)（索引页，正文以本目录 Markdown 为准）。
