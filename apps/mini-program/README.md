# uni-app 小程序（pnpm workspace 包 `mini-program`）

仓管员**上架 / 拣货**作业面，调用与 web-admin 相同的 FastAPI API。

**开发文档（权威）**：[`docs/mini-program/README.md`](../../docs/mini-program/README.md)  
**UI 设计**：[`design-system/wms/MASTER-MINI.md`](../../design-system/wms/MASTER-MINI.md) + [`design-system/wms/pages/`](../../design-system/wms/pages/)

## 前置

- Node 22（见 `apps/.nvmrc`）
- [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)（预览/调试/上传）

## 开发

在 `apps/` 目录：

```bash
pnpm install

# H5 预览（浏览器，可走 Vite 代理 /api）
pnpm dev:mini-program:h5

# 微信小程序编译（产物供微信开发者工具导入）
pnpm dev:mini-program:weixin
```

微信小程序：在微信开发者工具中导入 `apps/mini-program/dist/dev/mp-weixin/`。

## 环境变量

复制 `.env.example` 为 `.env`：

- **H5**：`VITE_API_BASE_URL` 留空，默认代理到 `http://localhost:8000`
- **微信小程序**：填写完整 API 根地址；本地开发可在开发者工具中关闭「不校验合法域名」

## 常用命令

```bash
pnpm typecheck:mini-program
pnpm test:mini-program
pnpm build:mini-program:weixin

# API 契约变更后：同步 snapshot 并重新生成类型
pnpm --filter web-admin generate:openapi-snapshot
cp web-admin/openapi.snapshot.json mini-program/openapi.snapshot.json
pnpm --filter mini-program generate:api
```

CI：变更 `apps/mini-program/**` 等路径时，GitHub Actions `mini-program-test.yml` 会跑 typecheck + unit test（与本地上述命令一致）。

## MVP 页面

| 页面 | 说明 |
|---|---|
| 登录 | 仅 `operator` 仓管员 |
| Tab·待办 | 待上架 / 待拣货单据 |
| Tab·我的 | 身份、仓库、退出 |
| 入库详情 → 上架 | 按行上架 |
| 出库详情 → 拣货 | 按行实扣（库位只读=审核分配） |

路由与 API 映射见 [`docs/mini-program/pages.md`](../../docs/mini-program/pages.md)。Spec：[#32](https://github.com/Zoti321/wms/issues/32)。

## 说明

使用 uni-app CLI（Vite），**无需 HBuilderX**。类型检查与单元测试与 web-admin 一样在 Cursor/VSCode 中完成。

编辑器需安装 [Vue - Official](https://marketplace.visualstudio.com/items?itemName=Vue.volar) 扩展；修改 `tsconfig.json` 后执行「TypeScript: Restart TS Server」刷新类型提示。
