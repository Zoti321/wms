# Staging 上重跑后端 UAT

与本地使用**同一套** `tests/uat` 剧本；仅通过 `UAT_BASE_URL` 切换 HTTP 目标。唯一测试缝仍为 `/api/v1` 黑盒。

## 最小前提

1. **迁移**：`alembic upgrade head` 已执行到当前仓库 head
2. **种子账号**（非生产 `APP_ENV` 下由迁移写入，口令勿提交仓库）：
   - `admin` / `supervisor` / `operator` / `viewer`
   - 默认口令与开发种子相同（`Admin@123456`）；生产须单独维护
3. **网络**：API 源站 HTTP/HTTPS 可达；路径前缀 `/api/v1`
4. **健康**（可选预检）：`GET /health` 返回 200 且 `checks.database` 为 `ok`（见 issue #14）

每个 UAT 场景自建仓库/SKU/库位（唯一编码），**不需要**清库；可重复跑。

## 环境变量

在 `services/wms-api` 目录：

| 变量 | 说明 |
|---|---|
| `UAT_BASE_URL` | API 源站，**不含**路径。例：`https://staging.example.com` 或 `http://127.0.0.1:8000` |
| `UAT_PASSWORD` | 种子账号口令（默认 `Admin@123456`） |
| `UAT_ADMIN_USERNAME` 等 | 覆盖默认用户名（通常不必设） |

设置 `UAT_BASE_URL` 后，套件**不再**连接本地 MySQL，也不走 TestClient。

## 本地对 staging 实例

```bash
cd services/wms-api

export UAT_BASE_URL="https://staging.example.com"
uv run pytest tests/uat -v --fail-on-skipped
```

## GitHub Actions

仓库 **Actions → wms-api UAT gate → Run workflow**：

- `uat_base_url` 留空：CI 内 MySQL 8 + TestClient（与本地等效）
- 填写 staging URL：对真实部署发 HTTP（MySQL 服务容器仍启动但不会被 UAT 使用）

绿灯后在 PR / 发版记录中保存 Actions Run URL 与 commit SHA（追溯见 [`uat-coverage.md`](./uat-coverage.md)）。

## 常见问题

| 现象 | 排查 |
|---|---|
| 401 登录失败 | 种子是否存在、口令是否与环境一致 |
| 403 批量出现 | staging 是否误用 `APP_ENV=prod` 且无种子 |
| 连接超时 | 防火墙、`UAT_BASE_URL` 是否误带 `/api/v1` 后缀 |
| 409 盘点/锁冲突 | 通常不应在 staging 发生（场景自建数据）；检查是否共用脏库 |

## 观测缺口

无法经只读 API 观测的条目见 [`services/wms-api/tests/uat/README.md`](../../services/wms-api/tests/uat/README.md#观测缺口)。不得改为直连数据库验收。
