# uni-app 小程序（pnpm workspace 包 `mini-program`）

仓管员上架/拣货作业面，调用与 web-admin 相同的 FastAPI API。

## 前置

- Node ≥ 20.19（见 `apps/.nvmrc`）
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
```

## 说明

使用 uni-app CLI（Vite），**无需 HBuilderX**。类型检查与单元测试与 web-admin 一样在 Cursor/VSCode 中完成。
