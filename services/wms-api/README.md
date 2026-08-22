# wms-api

仓脉 WMS 后端（FastAPI + MySQL 8.0 + uv）。领域包与 `src/*/CONTEXT.md` 对齐：`catalog` / `inventory` / `inbound` / `outbound` / `stocktake`；`platform` 为身份、操作日志与只读基础报表。

## 本地启动

```bash
# 仓库根目录：启动 MySQL（账号见下方，与 .env.example 一致）
docker compose up -d mysql

cd services/wms-api
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --app-dir .
```

健康检查：`GET /health`（JSON：`status` + `checks.database`；DB 不可达 HTTP 503；本地无库可设 `HEALTH_CHECK_DB=false`）  
备份恢复：见仓库根 `docs/runbooks/mysql-backup-restore.md`
登录：`POST /api/v1/auth/login`（body：`{"username":"admin","password":"Admin@123456"}`）  
主数据（需 Bearer）：`/api/v1/warehouses`、`/skus`、`/locations`、`/suppliers`、`/customers`；删除一律 `POST .../{id}/deactivate`（停用，不物理删除）。库位空间状态字段为 `space_status`（idle/occupied/frozen），勿与库存冻结数量混淆。  
入库：`GET /api/v1/inbound-orders`（列表，支持 `warehouse_id`/`status`/`page`/`page_size`）；`POST /api/v1/inbound-orders`（submit / approve / putaway / cancel）；上架必须带 `Idempotency-Key`，经库存 `increase` 记账。  
出库：`GET /api/v1/outbound-orders`（列表，查询参数同上）；`POST /api/v1/outbound-orders`（submit / approve / pick / cancel）；审核=分配、拣货=实扣、取消未拣=释放预留；approve/pick/cancel 必须带 `Idempotency-Key`。  
盘点：`GET /api/v1/stocktakes`（列表，查询参数同上）；`POST /api/v1/stocktakes`（创建并加盘点锁 / counts 实盘 / approve 调账释锁 / cancel 释锁）；create/approve/cancel 必须带 `Idempotency-Key`；审核需 `stocktake:approve`（admin/supervisor）。  
列表响应 `data` 形如 `{ "items": [...], "total": N, "page": P, "page_size": S }`；默认按 `created_at` 倒序；`page_size` 默认 20、上限 100。  
库存查询：`GET /api/v1/inventories`、`GET /api/v1/inventories/ledgers`、`GET /api/v1/inventories/alerts`。  
基础报表（需 `report:read`：admin/supervisor/viewer；operator 默认无）：  
`GET /api/v1/reports/daily?warehouse_id=&business_date=`（JSON）、`GET /api/v1/reports/daily.csv?...`（CSV 直出）。  
`business_date` 为 UTC 日历日 `YYYY-MM-DD`。字段口径：当日有上架的入库单数与上架量、当日有拣货的出库单数与实扣量、当前有货 SKU 数、当前总可用、有效预警条数。报表只读聚合，不改库存账。

### OpenAPI 交互文档

非生产环境（`APP_ENV` 非 `prod`/`production`）可浏览器打开：

| 入口 | 说明 |
|---|---|
| [`/docs`](http://127.0.0.1:8000/docs) | Swagger UI：Authorize 后可直接试调 |
| [`/redoc`](http://127.0.0.1:8000/redoc) | ReDoc 只读浏览 |
| [`/openapi.json`](http://127.0.0.1:8000/openapi.json) | OpenAPI 3 契约 |

试调步骤：先 `POST /api/v1/auth/login` → 右上角 **Authorize** 填入 `access_token` → 再调受保护接口。生产环境上述三个入口均关闭（404）。

### Docker Compose 连接

`docker-compose.yml` 中 MySQL：`wms` / `wms`，库名 `wms`，root 密码 `root`。  
API 全栈 profile 覆盖为 `mysql+pymysql://wms:wms@mysql:3306/wms?charset=utf8mb4`。  
若本机曾用旧凭据初始化过数据卷，需 `docker compose down -v` 后重建（会清空本地库）。

### 开发种子账号

迁移在非生产环境（`APP_ENV` 非 `prod`/`production`）写入开发种子账号（口令均为 `Admin@123456`）：

| username | role | 说明 |
|---|---|---|
| `admin` | `admin` | 系统管理员（全权限） |
| `supervisor` | `supervisor` | 仓库主管（可审核） |
| `operator` | `operator` | 仓管员（执行入出库，不可审核） |
| `viewer` | `viewer` | 只读（查询，不可写） |

操作日志：`GET /api/v1/operation-logs`；字典：`GET /api/v1/dictionaries`（admin 可 `POST`/`PATCH`/`POST .../deactivate`）；用户：`GET /api/v1/users`、`POST /api/v1/users`、`POST .../deactivate`、`POST .../reset-password`、`PATCH .../role`（均需 `user:write`）。`GET /auth/me` 返回 `permissions` 权限码数组。

**请勿把生产口令写进仓库。** 修改种子密码示例：

```bash
# 生成 bcrypt 哈希后更新 users 表
uv run python -c "import bcrypt; print(bcrypt.hashpw(b'你的新密码', bcrypt.gensalt()).decode())"
```

```sql
UPDATE users SET password_hash = '<新哈希>' WHERE username = 'admin';
```

## 测试

需要可达的 MySQL（默认连接与 `.env.example` 相同）。可选 `TEST_DATABASE_URL` 指向隔离库。

```bash
uv run pytest
```

发版/上线前另跑后端 UAT（独立套件，日常 PR 不收集）：

```bash
uv run pytest tests/uat
```

说明、staging 前提（`UAT_BASE_URL`）与观测缺口见 [`tests/uat/README.md`](./tests/uat/README.md)。  
发版 UAT 门禁 CI：[`.github/workflows/wms-api-uat.yml`](../../.github/workflows/wms-api-uat.yml)（手动触发）。  
人工抽查与 API 步骤：[`docs/uat/backend-signoff.md`](../../docs/uat/backend-signoff.md)；staging 指南：[`docs/uat/staging-uat.md`](../../docs/uat/staging-uat.md)。

若本机无 MySQL：集成测试会 `pytest.skip`（不注入假登录旁路）。

### CI（GitHub Actions）

PR 与 push 到 `main` 时，当变更涉及 `services/wms-api/**` 或 workflow 自身，会自动运行 [`.github/workflows/wms-api-test.yml`](../../.github/workflows/wms-api-test.yml)：

1. 启动 MySQL 8.0 服务容器（凭据与 `docker-compose.yml` 一致：`wms`/`wms`，库 `wms`）
2. `uv sync --frozen`（缓存依赖）→ `uv run pytest -v --tb=short --ignore=tests/uat --fail-on-skipped`
3. 迁移由测试 `conftest` 会话夹具执行 `alembic upgrade head`（与本地一致）
4. 日常 CI **不收集** `tests/uat`（与本地默认 `pytest` 相同）

**发版/上线前**在 GitHub Actions 手动运行 [`.github/workflows/wms-api-uat.yml`](../../.github/workflows/wms-api-uat.yml)，或本地 `uv run pytest tests/uat`。可选 workflow 输入 `uat_base_url` 对 staging 重跑；详见 [`docs/uat/staging-uat.md`](../../docs/uat/staging-uat.md)。
