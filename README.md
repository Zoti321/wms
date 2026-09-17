# 仓脉 WMS

单据驱动、库存唯一账本、出库软分配的仓库管理系统。交付面：FastAPI 后端、Vue 3 网页后台、uni-app 微信小程序作业端。

## 快速开始

| 目标 | 入口 |
|------|------|
| 人类阅读文档 | [`docs/index.html`](docs/index.html) 或 `./scripts/open-docs.sh` |
| 文档地图（Markdown） | [`docs/README.md`](docs/README.md) |
| 领域术语 | [`CONTEXT-MAP.md`](CONTEXT-MAP.md) → `src/*/CONTEXT.md` |
| 模块需求（SRS） | [`docs/domains/README.md`](docs/domains/README.md) |
| 开发设计 | [`docs/dev/README.md`](docs/dev/README.md) |
| 后端本地运行 | [`services/wms-api/README.md`](services/wms-api/README.md) |
| 网页后台 | [`apps/web-admin/README.md`](apps/web-admin/README.md) |
| 小程序 | [`docs/mini-program/README.md`](docs/mini-program/README.md) |
| Agent 读法 | [`AGENTS.md`](AGENTS.md) |

## 仓库结构

Monorepo：`apps/`（pnpm）+ `services/wms-api/`（uv）+ `src/*/CONTEXT.md`（领域术语，与后端包名对齐）。
