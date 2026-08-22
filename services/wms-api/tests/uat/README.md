# 后端用户验收（UAT）

发版/上线前必过的 API 黑盒套件。日常 `uv run pytest` **不收集**本目录，避免拖慢 PR 回归。

## 测试缝

唯一缝：HTTP `/api/v1`。不断言 ORM、不直连改库存表。本地默认走应用 ASGI `TestClient`；设置 `UAT_BASE_URL` 后对同一剧本发真实 HTTP。

## 怎么跑

在 `services/wms-api` 目录：

```bash
# 本地（需可达 MySQL；与日常集成测相同 skip 策略）
uv run pytest tests/uat

# staging / 已部署实例
# PowerShell
$env:UAT_BASE_URL="https://staging.example.com"
uv run pytest tests/uat
```

`UAT_BASE_URL` 为 API 源站（不含路径），例如 `http://127.0.0.1:8000`。剧本仍请求 `/api/v1/...`。

可选环境变量：`UAT_PASSWORD`（默认与开发种子 `Admin@123456` 相同）、`UAT_ADMIN_USERNAME` / `UAT_SUPERVISOR_USERNAME` / `UAT_OPERATOR_USERNAME` / `UAT_VIEWER_USERNAME`。

无 MySQL 且未设 `UAT_BASE_URL`：与日常集成测一致，`pytest.skip`，不假绿。

## Staging 最小前提

不在本套件内建设运维平台。对已有环境跑剧本前需满足：

1. 迁移已执行到当前 head
2. 非生产角色种子可用：`admin` / `supervisor` / `operator` / `viewer`
3. HTTP 或 HTTPS 可达，路径前缀为 `/api/v1`
4. `APP_ENV` 非生产时种子口令才由迁移写入；生产口令不得提交进仓库

每个场景自建仓库/SKU/库位（唯一编码），不依赖清空库，可并行或重复跑。

## 门禁

- 发版/上线前：`uv run pytest tests/uat` 必须绿灯
- 日常 PR：仍只跑 `uv run pytest`（不含本套件）
- 自动化绿灯后，按 [签字清单](../../../docs/uat/backend-signoff.md) 由系统管理员、仓库主管、仓管员各抽查一条关键路径

## 观测缺口

需求验收若无法经现有只读 API 观测，不得改为直连数据库，应记入此处：

| 条目 | 观测方式 | 说明 |
|---|---|---|
| 盘点锁覆盖哪些库位 | 对被锁库位上架/拣货返回 409，释锁后写操作成功 | 无「列出盘点锁」只读接口 |
| 日报 CSV | `Content-Type: text/csv` 与单元格 | CSV 不是 JSON 信封（`code/message/data/traceId`） |

当前无「必须扩 API 才能签字」的阻塞缺口。

## 范围外

Web/小程序 UI、压测、备份演练、波次/FEFO/调拨/ERP/红冲/Refresh Token 等 MVP 范围外能力。
