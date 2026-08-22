# 仓脉 WMS 网页后台

Vue 3 + TypeScript + Vite + Element Plus 管理端，见仓库 `docs/adr/0003-web-admin-vue-element-plus.md`。

## 开发

```bash
# 仓库根目录
pnpm install
pnpm dev:web-admin
```

默认 `http://localhost:5173`，API 经 Vite 代理转发至 `http://localhost:8000/api`。

## 脚本

| 命令 | 说明 |
|------|------|
| `pnpm dev:web-admin` | 启动开发服务器 |
| `pnpm typecheck:web-admin` | TypeScript 检查 |
| `pnpm test:web-admin` | Vitest 单测 |
| `pnpm --filter web-admin generate:api` | 从本地 OpenAPI 生成类型（需 API 运行） |

## 环境变量

复制 `.env.example` 为 `.env`。本地开发可留空 `VITE_API_BASE_URL` 以使用代理。
