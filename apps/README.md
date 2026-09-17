# 前端交付面（pnpm workspace）

Node / pnpm 工具链仅在此目录使用；后端见 `services/wms-api/`（uv）。

```bash
cd apps
pnpm install
pnpm dev:web-admin
```

小程序（uni-app）：

```bash
pnpm dev:mini-program:h5       # 浏览器预览
pnpm dev:mini-program:weixin   # 编译微信小程序 → dist/dev/mp-weixin
```

详见 `mini-program/README.md`。
