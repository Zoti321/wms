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

### Docker Compose 连接

`docker-compose.yml` 中 MySQL：`wms` / `wms`，库名 `wms`，root 密码 `root`。  
API 全栈 profile 覆盖为 `mysql+pymysql://wms:wms@mysql:3306/wms?charset=utf8mb4`。  
若本机曾用旧凭据初始化过数据卷，需 `docker compose down -v` 后重建（会清空本地库）。

### 开发种子管理员

迁移在非生产环境（`APP_ENV` 非 `prod`/`production`）写入开发种子账号：

| 字段 | 值 |
|---|---|
| username | `admin` |
| password | `Admin@123456` |
| role | `admin` |

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
