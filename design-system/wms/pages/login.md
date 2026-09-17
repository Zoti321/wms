# Page Override — 登录

> Master: [`../MASTER-MINI.md`](../MASTER-MINI.md)

## 目标

仓管员账号密码登录；非 `operator` 角色进入无权空态。

## 布局

```
┌─────────────────────────────┐
│         （系统导航栏）        │
│                             │
│         [Logo 120rpx]       │
│         仓脉 WMS 作业        │
│                             │
│  ┌─────────────────────┐   │
│  │ 用户名               │   │
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │ 密码                 │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │      登  录          │   │  ← 主按钮 96rpx
│  └─────────────────────┘   │
│                             │
└─────────────────────────────┘
```

- 背景：`$color-background`
- 表单区：可选白卡片 `--space-lg` padding，或裸表单 + gutter
- Logo：使用 `static/logo.png`

## 组件

| 元素 | 规范 |
|---|---|
| 输入框 | uni-ui `uni-easyinput`，高度 88rpx，`font-size: 28rpx` |
| 主按钮 | 全宽，Primary，loading 态禁重复提交 |
| 错误 | 表单上方红色文案区，展示 API `message` |

## 交互

1. 点击登录 → 按钮 loading → `POST /auth/login`
2. 成功 → `GET /auth/me` → 判断 `role_code`
3. `operator` → `uni.reLaunch({ url: '/pages/todo/index' })`
4. 其他 → `reLaunch` 无权页（或同页切换空态组件）

## 无障碍

- 输入框有 label（可见或 `aria`-等价属性）
- 密码允许粘贴
- 错误读屏可读

## 空态 / 无权

若在同页展示无权态：隐藏表单，居中 illustration + 标题 +「退出」按钮。

## API

见 `docs/mini-program/auth.md`。
