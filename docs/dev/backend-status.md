# 后端实现状态与缺口

本节记录 `services/wms-api` 相对 MVP 需求（[`docs/domains/`](../domains/README.md)）与 [里程碑](./milestones.md) 的**当前完成度与待办**。Agent / 开发者接后端任务前先读本节，避免重复盘点。

## 里程碑完成度

| 阶段 | 状态 | 说明 |
|------|------|------|
| M0 开工 | 已完成 | Monorepo、uv、FastAPI 骨架、登录、Alembic（`0001_m0`） |
| M1 主数据 | 已完成 | 仓库/SKU/库位/供应商/客户 CRUD + 停用（`0002_m1`）；RBAC 权限码 |
| M2 入库闭环 | 已完成 | 入库单 + 部分上架 + 库存增账 + 流水（`0003_m2`） |
| M3 出库闭环 | 已完成 | 分配预留 + 拣货实扣 + 取消释放 + 乐观锁防超卖（`0004_m3`） |
| M4 盘点报表 | 已完成 | 盘点锁、盈亏调账、库存预警、日报 JSON/CSV、操作日志（`0005_m4`–`0007_m6`） |
| M5 上线 | 进行中 | UAT 已纳入 PR/main CI；小程序作业面主路径已交付、typecheck/test 门禁已纳入；压测仍待 |

## 已实现模块（API 概览）

| 包 | 已实现路由 |
|----|-----------|
| `platform` | `POST /auth/login`、`GET /auth/me`（含 `permissions`）；`GET /operation-logs`（列表分页）；`GET /dictionaries`（列表分页）、`POST /dictionaries`、`PATCH /dictionaries/{id}`、`POST .../deactivate`；`GET /users`（列表分页）、`POST /users`、`POST /users/{id}/deactivate`、`POST /users/{id}/reset-password`、`PATCH /users/{id}/role`；`GET /reports/daily`、`GET /reports/daily.csv` |
| `catalog` | 仓库 / SKU / 库位 / 供应商 / 客户：列表分页、详情、创建、更新、`POST .../deactivate` |
| `inventory` | `GET /inventories`、`GET /inventories/ledgers`、`GET /inventories/alerts`（只读列表分页；写路径经 application 端口供其它上下文调用） |
| `inbound` | `GET /inbound-orders`（列表分页）、`POST /inbound-orders`、`GET /inbound-orders/{id}`、`PATCH ...`、submit / approve / putaway / cancel |
| `outbound` | `GET /outbound-orders`（列表分页）、`POST /outbound-orders`、`GET /outbound-orders/{id}`、`PATCH ...`、submit / approve / pick / cancel |
| `stocktake` | `GET /stocktakes`（列表分页）、`POST /stocktakes`、`GET /stocktakes/{id}`、counts / approve / cancel |

写操作幂等：上架、出库 approve/pick/cancel、盘点 create/approve/cancel 须请求头 `Idempotency-Key`。OpenAPI 与 README 见 `services/wms-api/`。

## 测试与验收门禁

| 套件 | 位置 | 用途 | 当前 |
|------|------|------|------|
| 日常集成测 | `services/wms-api/tests/`（不含 `uat/`） | PR 回归 | 120 用例；需可达 MySQL |
| 后端 UAT | `services/wms-api/tests/uat/` | 发版/上线门禁（纯自动化） | 24 用例；PR/main CI 自动跑；staging 可 `UAT_BASE_URL` 重跑 |
| Web Admin E2E | `apps/web-admin/e2e/` | 前端核心路径（mock API） | PR/main CI 自动跑 Playwright |
| Mini-program | `apps/mini-program/` | 作业端 typecheck + Vitest | PR/main CI：`mini-program-test.yml`（path filter） |
| 需求追溯 | `docs/uat/uat-coverage.md` | 需求验收 ↔ UAT 用例对照 | 无人工签字 |

无 MySQL 且未设 `UAT_BASE_URL` 时集成测与 UAT 均 `pytest.skip`，不假绿。UAT 观测缺口登记见 `services/wms-api/tests/uat/README.md`。

## 待补齐（MVP 内）

以下缺口**不在**需求「MVP 范围外」之列，对接 Web 管理端或发版前建议优先处理。

### 管理端 API

只读列表分页（主数据、库存、操作日志、字典、用户）已与单据列表对齐 `page` / `page_size` 约定（#16）。

### 工程与运维（M5）

| 缺口 | 说明 |
|------|------|
| CI 流水线 | PR/main：`wms-api-test.yml`（MySQL 8 + 集成测 + UAT）；staging：`wms-api-uat.yml`（手动 + 可选 `uat_base_url`）；前端：`web-admin-test.yml`、`mini-program-test.yml`（typecheck + unit test） |
| 健康检查 | `GET /health` 探测 MySQL（`SELECT 1`）；失败 HTTP 503 + `degraded`；可选 `HEALTH_CHECK_DB=false` |
| 性能/压测 | 仅集成测覆盖轻量「并发分配不超卖」；无 P95 / 日单据量压测 |
| 备份恢复演练 | [Runbook](../runbooks/mysql-backup-restore.md) 已文档化；季度演练仍建议保留（运维流程，非业务 UAT） |
| 监控告警 | `GET /metrics`（Prometheus：HTTP 错误率/耗时、连接池、库存写路径 counter）；告警规则示例见 [Runbook](../runbooks/operational-monitoring.md)（#15） |

### 已知观测缺口（非阻塞）

- 无「列出当前盘点锁覆盖库位」只读 API；验收经对被锁库位上架/拣货返回 409 间接证明（见 UAT README）。
- 日报 CSV 直出，不走 JSON 信封（`code/message/data/traceId`）。

## 明确不在 MVP（二期）

以下能力在 [overview.md](../domains/overview.md)「MVP 范围外」已排除，**不算当前后端缺口**：Refresh Token、Redis 会话、PDA 扫码、波次拣货、保质期 FEFO、多仓调拨自动化、ERP 深度双向同步、红冲单细化。

## 建议优先级

1. **支撑 Web 管理端**：只读列表分页已完成（#16）；技术栈与 `apps/web-admin/` 骨架已定（[ADR-0003](../adr/0003-web-admin-vue-element-plus.md)）；下一步登录联调与各模块列表页对接。
2. **发版门禁**：PR/main CI 自动跑集成测 + UAT + Web Admin E2E；staging 部署后可选 `wms-api-uat.yml` + `UAT_BASE_URL`（见 [staging 指南](../uat/staging-uat.md)）。追溯见 [uat-coverage.md](../uat/uat-coverage.md)。
3. **生产就绪**：健康检查探 DB（已完成）、[备份 Runbook](../runbooks/mysql-backup-restore.md)（已完成）、[运行监控](../runbooks/operational-monitoring.md)（#15 已完成）。
