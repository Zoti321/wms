# 技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| 网页后台 | Vue 3 + TypeScript + Vite + Element Plus | 管理端；路由权限 + 表格/表单为主 |
| 小程序 | uni-app · 微信小程序 | 仓管员上架/拣货作业面；调同一套 API |
| 后端 | Python 3.12+ + FastAPI + uvicorn | REST；仅 Access JWT；密码 bcrypt；配置 pydantic-settings + `.env`；CORS 白名单；包管理 uv |
| 持久化 | MySQL 8.0（InnoDB）+ SQLAlchemy 2（同步 Session）+ PyMySQL + Alembic | 时间统一 **UTC**；库存写路径明确事务；本地可用 `mysql:8.0` |
| 缓存 / 队列 | MVP **不上** Redis / Celery | 幂等键与业务数据均落 MySQL；库存预警在余额变更后同步判定 |
| 测试 | pytest + httpx | API 与库存分配/实扣等集成测试；测试库可回滚或独立库 |
| 文档 | OpenAPI 3（FastAPI 自动生成） | 前后端/小程序契约 |
| 工程 | Monorepo（`apps/` 下 pnpm workspace；后端 API 用 uv） | 交付面按 apps / services 组织 |
| 部署 | Docker Compose + uvicorn | MVP：api + mysql；生产可再评估多 worker |

后端选型已定为 **FastAPI + MySQL 8.0 + uv**：驱动 PyMySQL，ORM 写路径同步 Session，密码 bcrypt，进程 uvicorn，配置 pydantic-settings，时间 UTC，测试 pytest + httpx。MVP 不上 Redis。预警在库存记账成功后同步判定。权衡见 [ADR-0001](../adr/0001-fastapi-sync-mysql-no-redis.md)。

网页后台选型已定为 **Vue 3 + TypeScript + Vite + Element Plus**：`apps/` 目录 pnpm workspace；`openapi-typescript` + axios 薄封装对接统一信封；Pinia 承载 auth/app 上下文；Access Token 存 sessionStorage；静态路由 + `meta.permission` 与后端权限码对齐。权衡见 [ADR-0003](../adr/0003-web-admin-vue-element-plus.md)；调研过程见 [web-admin-stack.md](../research/web-admin-stack.md)。

**库存事务、软分配、流水表、盘点锁**为不可妥协的设计约束。
