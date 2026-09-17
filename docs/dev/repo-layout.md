# 工程结构（Monorepo）

```
wms/
├── apps/
│   ├── package.json         # 前端 pnpm workspace 根
│   ├── pnpm-workspace.yaml
│   ├── web-admin/           # Vue3 网页后台
│   └── mini-program/        # 小程序作业端
├── services/
│   └── wms-api/             # FastAPI（uv 管理依赖）
│       ├── app/
│       │   ├── platform/    # iam + 操作日志
│       │   ├── catalog/
│       │   ├── inventory/
│       │   ├── inbound/
│       │   ├── outbound/
│       │   └── stocktake/
│       ├── alembic/         # MySQL 迁移
│       ├── tests/           # pytest + httpx
│       ├── .env.example
│       ├── pyproject.toml
│       └── uv.lock
├── src/                     # 领域术语 CONTEXT.md（与包名对齐，仅 glossary）
│   ├── catalog/CONTEXT.md
│   ├── inventory/CONTEXT.md
│   ├── inbound/CONTEXT.md
│   ├── outbound/CONTEXT.md
│   └── stocktake/CONTEXT.md
├── docs/
│   ├── dev/                 # 开发设计（本目录，Markdown 权威）
│   ├── domains/             # 模块化 SRS
│   ├── requirements/        # 已废弃，指针至 domains/
│   ├── adr/
│   └── mini-program/
├── CONTEXT-MAP.md
└── docker-compose.yml
```
