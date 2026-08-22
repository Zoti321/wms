# wms-api

仓脉 WMS 后端（FastAPI + MySQL 8.0 + uv）。领域包与 `src/*/CONTEXT.md` 对齐：`catalog` / `inventory` / `inbound` / `outbound` / `stocktake`；`platform` 为身份与操作日志。

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

健康检查：`GET /health`  
登录：`POST /api/v1/auth/login`（body：`{"username":"admin","password":"Admin@123456"}`）  
主数据（需 Bearer）：`/api/v1/warehouses`、`/skus`、`/locations`、`/suppliers`、`/customers`；删除一律 `POST .../{id}/deactivate`（停用，不物理删除）。库位空间状态字段为 `space_status`（idle/occupied/frozen），勿与库存冻结数量混淆。  
入库：`/api/v1/inbound-orders`（submit / approve / putaway / cancel）；上架必须带 `Idempotency-Key`，经库存 `increase` 记账。  
出库：`/api/v1/outbound-orders`（submit / approve / pick / cancel）；审核=分配、拣货=实扣、取消未拣=释放预留；approve/pick/cancel 必须带 `Idempotency-Key`。  
盘点：`/api/v1/stocktakes`（创建并加盘点锁 / counts 实盘 / approve 调账释锁 / cancel 释锁）；create/approve/cancel 必须带 `Idempotency-Key`；审核需 `stocktake:approve`（admin/supervisor）。  
库存查询：`GET /api/v1/inventories`、`GET /api/v1/inventories/ledgers`、`GET /api/v1/inventories/alerts`。

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

操作日志：`GET /api/v1/operation-logs`；字典：`GET /api/v1/dictionaries`；用户角色：`GET /api/v1/users`、`PATCH /api/v1/users/{id}/role`（管理员）。

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

若本机/CI 无 MySQL：集成测试会 `pytest.skip`（不注入假登录旁路）。CI 等价策略：提供 MySQL 服务（Compose service 或托管实例）并设置 `DATABASE_URL`/`TEST_DATABASE_URL` 后再跑 `pytest`。
