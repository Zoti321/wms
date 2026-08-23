# 仓脉 WMS 网页后台

Vue 3 + TypeScript + Vite + Element Plus 管理端，见仓库 `docs/adr/0003-web-admin-vue-element-plus.md`。

## 开发

```bash
cd apps
pnpm install
pnpm dev:web-admin
```

默认 `http://localhost:5173`，API 经 Vite 代理转发至 `http://localhost:8000/api`。

## 脚本

在 `apps/` 目录执行：

| 命令 | 说明 |
|------|------|
| `pnpm dev:web-admin` | 启动开发服务器 |
| `pnpm typecheck:web-admin` | TypeScript 检查 |
| `pnpm test:web-admin` | Vitest 单测 |
| `pnpm --filter web-admin generate:openapi-snapshot` | 从 FastAPI 导出 OpenAPI 快照（无需启动服务） |
| `pnpm --filter web-admin generate:api` | 由快照生成 `src/types/openapi.d.ts` |

## 环境变量

复制 `.env.example` 为 `.env`。本地开发可留空 `VITE_API_BASE_URL` 以使用代理。

## 与后端协作约定

- **包管理器**：在 `apps/` 下统一使用 **pnpm**（`packageManager: pnpm@10.22.0`），勿使用 npm / yarn 安装依赖。
- **列表分页**：后端只读列表的 `page_size` 上限为 **100**（见 `services/wms-api/app/shared/pagination.py`）。前端下拉、批量加载选项时使用 `src/constants/api.ts` 中的 `MAX_LIST_PAGE_SIZE`，勿硬编码更大的值；超过上限会收到 **422** 校验错误。
- **OpenAPI 类型**：契约变更后执行 `pnpm --filter web-admin generate:openapi-snapshot` 与 `generate:api` 更新 `openapi.d.ts`。
