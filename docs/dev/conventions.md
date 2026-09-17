# 开发规范

- 分支：`main` 保护；功能分支 `feature/*`；发版打 tag
- 提交信息：简体中文，说明「为什么」
- 领域用语与 [`CONTEXT-MAP.md`](../../CONTEXT-MAP.md) / 各 `src/*/CONTEXT.md` 一致，避免「冻结」一词混用
- 接口变更更新 OpenAPI；破坏性变更升 `/api/v2`
- 配置与密钥：pydantic-settings + `.env`（不入库）；Compose/环境变量注入
- 时间：DB 与 API 统一 UTC；前端/小程序展示再转本地
- CORS：开发环境白名单本地 Vite 源（默认 `http://localhost:5173`）；小程序不依赖浏览器 CORS
- Web Admin：JWT 存 sessionStorage；路由 `meta.permission` 与 `/auth/me` 权限码一致；API 类型从 `/openapi.json` 生成
- Web Admin 测试：Vitest 覆盖 auth/permission/API 封装；Playwright E2E 覆盖核心路径
- 库存单测/集成测必覆盖：分配不足、实扣、释放预留、乐观锁冲突、幂等、盘点锁拒绝进出（pytest + httpx）
- 禁止在 Controller 或 inbound/outbound 包直接 UPDATE `inventory`
- 操作日志与库存流水分表存储、分接口查询
