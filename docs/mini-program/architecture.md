# 架构与工程结构

文档编号 WMS-SDD-MINI-001 · 模块 `architecture`

## 技术栈

| 层级 | 选型 | 说明 |
|---|---|---|
| 框架 | uni-app 3 + Vue 3 + TypeScript | CLI（Vite），无需 HBuilderX |
| 目标平台 | 微信小程序（MVP 主交付） | H5 仅开发预览 |
| UI | `@dcloudio/uni-ui` + SCSS token | token 见 `MASTER-MINI.md` → `src/uni.scss` |
| 状态 | Pinia | `auth`、`app` 两个 store |
| API | `uni.request` 薄封装 | 对标 web-admin 信封与错误码 |
| 类型 | `openapi-typescript` 生成 `openapi.d.ts` | 独立维护，不跨包 import web-admin |
| 测试 | Vitest + vue-tsc | 与 web-admin 相同工具链 |

## 在 Monorepo 中的位置

```
apps/
├── pnpm-workspace.yaml
├── web-admin/          # 管理端（主管/管理员）
└── mini-program/       # 作业端（仓管员）← 本文档
services/
└── wms-api/            # 共用 REST API
design-system/wms/
├── MASTER.md           # Web Admin 设计系统
├── MASTER-MINI.md      # 小程序设计系统
└── pages/              # 页面级 UI override
docs/mini-program/      # 本目录（工程说明）
```

交付面是**适配器**，不是限界上下文；领域包仍在 `services/wms-api/app/{catalog,inventory,inbound,outbound,stocktake}`。

## 目录结构（目标）

实现 M5 作业面时，`apps/mini-program/` 建议布局：

```
src/
├── pages/
│   ├── login/login.vue
│   ├── todo/index.vue              # Tab·待办
│   ├── my/index.vue                # Tab·我的
│   ├── inbound/
│   │   ├── detail.vue
│   │   └── putaway.vue
│   └── outbound/
│       ├── detail.vue
│       └── pick.vue
├── components/                     # 任务卡片、状态 Tag、数量 Stepper 等
├── stores/
│   ├── auth.ts
│   └── app.ts
├── api/
│   ├── client.ts
│   ├── auth.ts
│   ├── inboundOrders.ts
│   ├── outboundOrders.ts
│   └── locations.ts
├── utils/
│   ├── tokenStorage.ts
│   ├── idempotency.ts
│   └── errorMessage.ts
├── constants/
│   ├── api.ts
│   └── labels.ts                   # 与 web-admin 对齐的状态文案
├── types/
│   ├── api.ts
│   └── openapi.d.ts
├── config/env.ts
├── uni.scss                        # 设计 token 映射
├── pages.json                      # 路由 + TabBar
├── manifest.json
├── App.vue
└── main.ts
```

## 路由与 TabBar

`pages.json` 要点：

- **TabBar（2 项）**：待办 `pages/todo/index`、我的 `pages/my/index`
- **非 Tab 页**：登录、入库/出库详情、上架/拣货执行；使用微信原生导航栏返回
- **登录页**不在 TabBar 内；未登录访问 Tab 页时重定向登录

详细路由与 API 映射见 [pages.md](./pages.md)。

## Pinia Store

### `auth`

- `accessToken`、`user`（`/auth/me` 结果）
- `login()`、`fetchMe()`、`logout()`
- Token 持久化：`uni.setStorageSync('wms_access_token', …)`（对标 web `sessionStorage`）

### `app`

- `warehouseId`：MVP 登录后从默认种子仓写入，只读展示在「我的」
- `clearWarehouse()`：登出时清理

不在小程序维护菜单权限树；作业端能力由 **角色门禁**（`operator`）+ API 403 兜底。

## 环境变量

复制 `apps/mini-program/.env.example`：

| 变量 | H5 开发 | 微信小程序 |
|---|---|---|
| `VITE_API_BASE_URL` | 留空（Vite 代理 `/api`） | 完整 HTTPS API 根（如 `https://api.example.com`） |

微信小程序须在开发者工具配置合法域名；本地可临时关闭「不校验合法域名」。

## 常用命令

在 `apps/` 目录：

```bash
pnpm install
pnpm dev:mini-program:h5          # 浏览器预览
pnpm dev:mini-program:weixin      # 编译到 dist/dev/mp-weixin
pnpm typecheck:mini-program
pnpm test:mini-program
pnpm build:mini-program:weixin
```

微信开发者工具导入目录：`apps/mini-program/dist/dev/mp-weixin/`。

## 与 Web Admin 的差异

| 维度 | Web Admin | 小程序 |
|---|---|---|
| 用户 | 主管、管理员、仓管员 | **仅仓管员**（`operator`） |
| 布局 | 侧边栏 + 表格 | Tab + 卡片列表 + 执行页 |
| HTTP | axios | `uni.request` |
| Token 存储 | sessionStorage | uni.storage |
| 设计系统 | `MASTER.md` + Element Plus | `MASTER-MINI.md` + uni-ui |
| 列表 UI | `el-table` 高密度 | 卡片 + 大触控区 |

## 设计文档检索约定

构建某一页时：

1. 读 `design-system/wms/MASTER-MINI.md`
2. 读 `design-system/wms/pages/<page-name>.md`（若存在则 **override** Master）
3. 读本文档 [pages.md](./pages.md) 对应节的 API 映射
