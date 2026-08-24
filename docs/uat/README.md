# 后端 UAT 交付物索引

Issue #9 交付：独立 API 黑盒验收套件 + CI 发版门禁（**纯自动化，无人工签字**）。

## 自动化

| 项 | 位置 |
|---|---|
| UAT 套件（24 用例） | [`services/wms-api/tests/uat/`](../../services/wms-api/tests/uat/) |
| 套件说明与观测缺口 | [`services/wms-api/tests/uat/README.md`](../../services/wms-api/tests/uat/README.md) |
| 需求 ↔ 用例追溯 | [`uat-coverage.md`](./uat-coverage.md) |
| 日常 PR 集成测 | [`services/wms-api/tests/`](../../services/wms-api/tests/)（不含 `uat/`） |

本地跑 UAT（需 MySQL，或设 `UAT_BASE_URL` 对 staging）：

```bash
cd services/wms-api
uv run pytest tests/uat -v --fail-on-skipped
```

## CI 门禁

| 流水线 | 触发 | 范围 |
|---|---|---|
| [wms-api-test.yml](../../.github/workflows/wms-api-test.yml) | PR / push `main`（`services/wms-api/**`） | 集成测 + **UAT** |
| [wms-api-uat.yml](../../.github/workflows/wms-api-uat.yml) | **手动** `workflow_dispatch` | 可选 `uat_base_url` 对 staging 重跑同一 UAT 剧本 |
| [web-admin-test.yml](../../.github/workflows/web-admin-test.yml) | PR / push `main`（`apps/web-admin/**`） | 类型检查、单测、Playwright E2E（mock API） |

**发版判定：** `wms-api-test` 与 `web-admin-test` 在目标 commit 上均为绿灯；若对 staging 部署，再手动跑 `wms-api-uat` 并填写 staging URL。

## 术语

与 `CONTEXT-MAP.md` 一致：**盘点锁** ≠ 冻结数量；**库存流水** ≠ 操作日志。
