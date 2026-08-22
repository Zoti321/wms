# MVP：网页后台 Vue 3 + Element Plus + pnpm workspace

仓脉 WMS 网页后台（`apps/web-admin/`）选定 **Vue 3 + TypeScript + Vite + Element Plus**，根目录 **pnpm workspace** 管理前端包；后端仍为 ADR-0001 的 FastAPI，契约以 `/openapi.json` 为准。

**API 层**：`openapi-typescript` 生成类型，axios 薄封装统一解包 `{ code, message, data, traceId }` 并附加 JWT。**状态**：Pinia 仅承载 auth（token、user、permissions）与 app 上下文（如当前仓库）；其余页面级 state 不上升全局。**鉴权**：Access Token 存 **sessionStorage**（MVP 无 Refresh，480 分钟过期重登）；静态路由表 + `meta.permission` 与后端权限码 1:1，路由守卫拦截未授权页，按钮用 `v-permission`。**测试**：Vitest 覆盖 permission 工具与 API 封装；E2E 待核心流贯通后再加。

**未选**：React 栈（与 SDD 不一致且无复用收益）；动态后端菜单 JSON（MVP 菜单稳定）；Turborepo（仅一个前端 app）；localStorage 存 Token（标签页关闭不应长期保留会话）。
