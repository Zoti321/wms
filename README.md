# 仓脉 WMS

单据驱动、库存唯一账本、出库软分配的企业级仓库管理系统。

## 系统概要

系统分为**业务模块**与**平台模块**，并额外提供**微信小程序作业端**供仓管员现场上架与拣货。业务以「入库单 / 出库单 / 盘点单 + 库存流水」为主线，平台负责身份权限、字典、操作审计与基础报表。

与经典进销存演示项目 [yeqifu/warehouse](https://github.com/yeqifu/warehouse) 相比，仓脉侧重**库位级账实一致、出库预留与实扣分离、盘点锁与流水追溯**；功能对照与缺口见 [`docs/dev/warehouse-comparison.md`](docs/dev/warehouse-comparison.md)。

## 功能模块

### 一、业务模块

#### 1、主数据管理

- 仓库、SKU（商品）、库位（区 / 排 / 位）
- 供应商、客户
- 列表分页与模糊查询
- 创建、更新、停用（保留历史，不物理删除）

#### 2、入库管理

- 入库单列表与分页（按仓库、状态筛选）
- 类型：采购入库、退货入库、其他入库
- 草稿 → 待审核 → 已审核 → 按行上架 → 已完成 / 已取消
- 支持部分上架；盘点锁库位拒绝上架

#### 3、出库管理

- 出库单列表与分页
- 类型：销售出库、领料出库、其他出库
- 审核分配（软预留）→ 拣货实扣 → 完成；取消释放未拣预留
- 并发分配乐观锁，防止超卖

#### 4、库存管理

- 库存余额查询（按仓库 / SKU / 库位）
- 库存流水追溯（关联业务单据与单据行）
- 低库存预警（基于 SKU 安全库存阈值）

#### 5、盘点管理

- 盘点单创建、实盘录入、审核调账
- 盘点锁期间，被锁库位禁止上架与出库

### 二、平台模块

#### 1、用户登录

- 账号密码登录，签发 Access JWT
- 未登录访问受保护资源返回 401
- 按角色权限码（RBAC）鉴权

#### 2、用户管理

- 用户列表与分页
- 用户创建、停用、重置密码
- 为用户分配角色（admin / supervisor / operator / viewer）

#### 3、字典配置

- 业务字典维护（单位、单据类型、取消原因等）

#### 4、操作日志

- 登录、审核等敏感操作审计
- 按时间、操作人查询

#### 5、基础报表

- 仓库日报（JSON / CSV 导出）

> **相对参考项尚未覆盖**：动态菜单与角色 CRUD、部门树、登录验证码、系统公告、缓存管理 UI、独立进销退货模块、商品图片上传。详见对比文档。

### 三、小程序作业端

- 仓管员登录（`operator` 角色）
- 待办：待上架入库单、待拣货出库单
- 按行上架、按行拣货（实扣）
- 与网页后台共用同一套 FastAPI

## 技术选型

| 层级 | 选型 |
|------|------|
| 网页后台 | Vue 3 + TypeScript + Vite + Element Plus |
| 小程序 | uni-app · 微信小程序 |
| 后端 | Python 3.12+ · FastAPI · uvicorn · uv |
| 持久化 | MySQL 8.0 · SQLAlchemy 2 · Alembic |
| 鉴权 | JWT + bcrypt · 权限码 RBAC |
| 测试 | pytest + httpx · Playwright E2E · 自动化 UAT |
| 部署 | Docker Compose（api + mysql） |

详细说明见 [`docs/dev/stack.md`](docs/dev/stack.md)。

## 开发环境

| 项 | 要求 |
|----|------|
| 操作系统 | Windows / macOS / Linux |
| 运行时 | Node.js 20+、Python 3.12+、Docker |
| 包管理 | pnpm（`apps/`）、uv（`services/wms-api/`） |
| 数据库 | MySQL 8.0（本地可用 Docker Compose） |
| 浏览器 | Chrome / Edge 近两个大版本（≥ 1280 宽） |
| 微信开发者工具 | 小程序调试（基础库 ≥ 2.19.2） |

## 快速开始

### 1. 启动数据库与 API

```bash
# 仓库根目录
docker compose up -d mysql

cd services/wms-api
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --app-dir .
```

API 默认 `http://localhost:8000`。开发种子账号：`admin` / `Admin@123456`（见 [`services/wms-api/README.md`](services/wms-api/README.md)）。

### 2. 启动网页后台

```bash
cd apps
pnpm install
pnpm dev:web-admin
```

默认 `http://localhost:5173`，API 经 Vite 代理至后端。

### 3. 小程序（可选）

见 [`apps/mini-program/README.md`](apps/mini-program/README.md) 与 [`docs/mini-program/README.md`](docs/mini-program/README.md)。

### 文档入口

| 目标 | 入口 |
|------|------|
| 人类阅读文档 | [`docs/index.html`](docs/index.html) 或 `./scripts/open-docs.sh` |
| 文档地图（Markdown） | [`docs/README.md`](docs/README.md) |
| 领域术语 | [`CONTEXT-MAP.md`](CONTEXT-MAP.md) → `src/*/CONTEXT.md` |
| 模块需求（SRS） | [`docs/domains/README.md`](docs/domains/README.md) |
| 开发设计 | [`docs/dev/README.md`](docs/dev/README.md) |
| 后端实现状态 | [`docs/dev/backend-status.md`](docs/dev/backend-status.md) |
| 参考项目对比 | [`docs/dev/warehouse-comparison.md`](docs/dev/warehouse-comparison.md) |
| Agent 读法 | [`AGENTS.md`](AGENTS.md) |

## 仓库结构

Monorepo：`apps/`（pnpm）+ `services/wms-api/`（uv）+ `src/*/CONTEXT.md`（领域术语，与后端包名对齐）。

```
wms/
├── apps/web-admin/      # Vue 3 网页后台
├── apps/mini-program/   # uni-app 小程序
├── services/wms-api/    # FastAPI 后端
├── docs/                # 需求、设计、调研
└── src/*/CONTEXT.md     # 领域术语表
```

完整结构见 [`docs/dev/repo-layout.md`](docs/dev/repo-layout.md)。

## 讨论

问题与需求请在本仓库 [GitHub Issues](https://github.com/Zoti321/wms/issues) 讨论。开发协作与 Agent 规范见 [`AGENTS.md`](AGENTS.md)。
