# 网页后台技术栈调研

> 调研日期：2026-08-22 · 分支：`feature/web-admin` · 结论已采纳并写入 [ADR-0003](../adr/0003-web-admin-vue-element-plus.md)

## 背景与约束

仓脉 WMS 网页后台是**交付面适配器**（见 `CONTEXT-MAP.md`），对接已有 FastAPI 后端（ADR-0001）。MVP 约束：

- 表格/表单为主的管理端；路由 + 按钮级 RBAC
- 后端仅 Access JWT，无 Refresh Token（`JWT_ACCESS_EXPIRE_MINUTES` 默认 480）
- 统一 API 信封 `{ code, message, data, traceId }`（`services/wms-api/app/shared/response.py`）
- `/auth/me` 返回 `permissions: string[]`，与接口 `require_permissions` 对齐
- CORS 开发默认 `http://localhost:5173`（`services/wms-api/app/shared/config.py`）
- Monorepo：`apps/`（pnpm workspace）+ `services/wms-api/`（uv）

## 推荐结论（已采纳）

| 决策点 | 选型 | 理由摘要 |
|--------|------|----------|
| SPA 框架 | Vue 3 + TypeScript | SDD 已定；与 Element Plus 官方组合；Vite 官方 `vue-ts` 模板 |
| 构建 | Vite | 默认 dev 端口 5173，与后端 CORS 一致；支持 monorepo root |
| UI 库 | Element Plus | B 端 Table/Form/Dialog 成熟；设计原则强调效率与可控性 |
| 包管理 | pnpm workspace | 仓库 SDD 约定；内置 monorepo，无需 MVP 引入 Turborepo |
| API 类型 | openapi-typescript + axios 薄封装 | FastAPI 暴露 `/openapi.json`；类型与契约同步；封装层解包信封 |
| 全局状态 | Pinia（auth + app 上下文） | 登录态与 `warehouse_id` 跨页共享；其余页面级 state |
| Token 存储 | sessionStorage | MVP 无 Refresh；关标签失效；比 localStorage XSS 面略小 |
| 路由权限 | 静态路由 + `meta.permission` + 守卫 | 与后端权限码 1:1；PR 可 review；MVP 菜单稳定 |
| 测试 | Vitest（auth/permission/API 封装）；E2E 延后 | 不阻塞 M1 主数据页 |

## 分项调研

### Vue 3 vs React

**Vue 3**（[Introduction \| Vue.js](https://vuejs.org/guide/introduction.html)）：渐进式框架，单文件组件适合表格页快速迭代；官方生态含 Vue Router、Pinia。

**React**：生态同样成熟，但本仓库 SDD 与目录结构已锚定 Vue 3（`docs/development.html` §2、§8），且无跨端复用需求（小程序独立）。**无足够理由在 MVP 阶段改栈**。

→ **Vue 3**（ADR 锁定）

### Element Plus vs Ant Design Vue vs Naive UI

**Element Plus**（[Design \| Element Plus](https://element-plus.org/en-US/guide/design.html)）：强调 Consistency、Efficiency、Controllability，与 WMS 单据审核、表格密集场景一致；[Table](https://element-plus.org/en-US/component/table.html) 组件覆盖分页、选择、固定列等管理端刚需。

**Ant Design Vue**：能力相当，团队若已有 Ant Design React 经验可考虑；本项无存量代码，遵循 SDD 即可。

**Naive UI**：TypeScript 友好、样式现代；国内 WMS/ERP 案例与中文社区资料相对少，表格高级模式需更多自研。

→ **Element Plus**（ADR 锁定）

### Vite

[Vite Getting Started](https://vite.dev/guide/)：dev server 默认 `http://localhost:5173`，与 `CORS_ORIGINS` 默认值一致；文档明确支持 monorepo root 解析；官方 `vue-ts` 模板可直接 scaffold 到 `apps/web-admin/`。

→ **Vite**（随 Vue 栈 ADR 锁定）

### OpenAPI 类型 vs 手写客户端

FastAPI 自动生成 OpenAPI（[FastAPI - Metadata and Docs URLs](https://fastapi.tiangolo.com/tutorial/metadata/)）；本仓库 `/openapi.json` 已在测试中验证（`services/wms-api/tests/test_openapi_docs.py`）。

**openapi-typescript**（[openapi-typescript](https://github.com/drwpow/openapi-typescript)）：从 OpenAPI 生成 TS 类型，零运行时；配合手写 axios 拦截器处理 JWT 与 `{ code, message, data }` 信封。

**完整 codegen client**（如 hey-api）：可减少样板代码，但对自定义信封需额外适配层；MVP 类型同步 + 薄封装足够。

→ **openapi-typescript + axios 薄封装**（实现细节，可逆；不单独 ADR）

### Pinia vs composables-only

[Pinia](https://pinia.vuejs.org/) 为 Vue 官方推荐状态库；本项仅需 `useAuthStore`（token、user、permissions）与 `useAppStore`（当前仓库）。页面级列表筛选、表单 state 用 composables/`ref` 即可。

→ **Pinia 最小集**（可逆）

### sessionStorage vs localStorage vs memory-only

[OWASP HTML5 Security Cheat Sheet - Local Storage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#local-storage)：Local Storage 与 Session Storage 均**不能**防 XSS 读取；Session Storage 作用域为标签页，关闭即清除。

MVP 无 Refresh Token，480 分钟过期后重登可接受；memory-only 会导致刷新即登出，管理端体验差。

→ **sessionStorage**（ADR 记录安全权衡）

### pnpm workspace vs Turborepo

[pnpm Workspaces](https://pnpm.io/workspaces)：`apps/pnpm-workspace.yaml` 联合 `web-admin`（及后续 `mini-program`）；MVP 仅一个前端 app。

Turborepo 擅长多包缓存与并行 task；待 `apps/mini-program/` 与 web-admin 并行 CI 再评估。

→ **pnpm workspace only**（ADR 锁定 monorepo 前端工程方式）

### 路由权限模型

后端权限码示例见 `services/wms-api/app/platform/domain/permissions.py`。前端：

1. 静态路由表，每条路由 `meta: { permission: 'catalog:read' }`
2. `router.beforeEach` 校验 token + permission
3. 侧边栏由路由表 filter 生成
4. 按钮 `v-permission="'inbound:approve'"` 与接口权限对齐

动态后端菜单 JSON 适合菜单频繁运营配置的场景；MVP 菜单与权限码同步发版即可。

→ **静态路由 + meta.permission**（ADR 记录）

### 测试范围

Vitest 与 Vite 同源配置，适合单测 `hasPermission()`、axios 信封解包、路由守卫逻辑。Playwright E2E（登录 → 主数据列表）在 M2 核心流贯通后补充。

→ **Vitest 先行，E2E 延后**（工程约定，可逆）

## ADR 边界

**应写入 ADR-0003（难逆转 / 有真实权衡）：**

- Vue 3 + TypeScript + Vite + Element Plus 栈
- pnpm workspace monorepo 前端工程
- sessionStorage 存 Access Token（含安全说明）
- 静态路由 + permission meta 的 RBAC 模型

**不必 ADR（易逆转或显而易见）：**

- axios vs fetch
- Vitest 范围
- 具体目录命名（`src/stores/auth.ts` 等）
- openapi-typescript 版本 pin

## 参考

- `docs/development.html` §2、§8、§9
- `docs/adr/0001-fastapi-sync-mysql-no-redis.md`
- `services/wms-api/app/platform/api/auth.py`
- `services/wms-api/app/platform/domain/permissions.py`
- [Vue.js Guide](https://vuejs.org/guide/introduction.html)
- [Vite Guide](https://vite.dev/guide/)
- [Element Plus](https://element-plus.org/en-US/guide/design.html)
- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Pinia](https://pinia.vuejs.org/)
- [openapi-typescript](https://github.com/drwpow/openapi-typescript)
- [OWASP HTML5 Security - Local Storage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#local-storage)
