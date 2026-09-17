# Design System — 仓脉 WMS 小程序（Master）

> **LOGIC:** 构建小程序某一页时，先读 `design-system/wms/pages/[page-name].md`。
> 若该文件存在，其规则 **override** 本 Master。
> Web Admin 规范见同目录 [`MASTER.md`](./MASTER.md)（Element Plus）；**不要**在小程序直接使用 Element Plus 组件。

---

**Project:** 仓脉 WMS · 作业端（Mini Program）  
**Stack:** uni-app 3 + Vue 3 + uni-ui + SCSS  
**Platform:** 微信小程序（MVP）  
**Theme:** 仅浅色  
**Design Dials:** Variance 3/10 | Motion 3/10 | Density 5/10（作业端适中，非 Dashboard 极密）

---

## 与 Web Master 的关系

| 维度 | Web `MASTER.md` | 本文件 `MASTER-MINI.md` |
|---|---|---|
| 主色 / 状态语义 | ✓ 继承 | ✓ 同色值 |
| 字体 | Fira Sans / Fira Code | **系统字体栈** |
| 布局 | 侧边栏 + 表格 36px | Tab + 卡片 + 大按钮 |
| 组件库 | Element Plus | uni-ui |
| 深色模式 | 可选 | **MVP 不做** |

---

## 设计原则

1. **单手操作**：主操作在屏幕下半部；底部固定 CTA ≥ 96rpx 高。
2. **手套友好**：可点击区域 ≥ 88rpx × 88rpx（约 44pt）。
3. **少输入多选择**：库位用搜索点选，数量用 Stepper；MVP 无扫码。
4. **状态可识别**：颜色 + 文字标签；红/绿不单靠颜色。
5. **弱网可理解**：加载 skeleton、失败 toast、写操作幂等重试。

---

## Color Palette（Light Only）

| Role | Hex | SCSS / CSS Variable | 用途 |
|---|---|---|---|
| Primary | `#1E40AF` | `$color-primary` / `--color-primary` | 主按钮、链接、选中 Tab |
| On Primary | `#FFFFFF` | `$color-on-primary` | 主按钮文字 |
| Success | `#16A34A` | `$color-success` | 完成、成功 toast |
| Warning | `#D97706` | `$color-warning` | 进行中、待处理 |
| Danger | `#DC2626` | `$color-danger` | 错误、库存预警 |
| Info | `#0284C7` | `$color-info` | 信息 Tag |
| Background | `#F1F5F9` | `$color-background` | 页面底 |
| Surface / Card | `#FFFFFF` | `$color-card` | 卡片 |
| Foreground | `#0F172A` | `$color-foreground` | 主文字 |
| Muted | `#64748B` | `$color-muted` | 次要文字 |
| Border | `#E2E8F0` | `$color-border` | 分割线、输入框边 |

映射到 `apps/mini-program/src/uni.scss` 时覆盖 `$uni-color-primary` 等为上述值。

---

## WMS 状态语义（与 Web 一致）

| 域 | 状态 | 颜色 | 小程序 Tag |
|---|---|---|---|
| 入库 | draft / pending / approved / putaway / done / cancelled | info / warning / primary / warning / success / default | `uni-tag` + 中文 |
| 出库 | draft / pending / approved / picking / done / cancelled | default / warning / primary / warning / success / info | 同上 |

中文文案：`apps/web-admin/src/constants/labels.ts`。

---

## Typography

```scss
$font-family-base: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
$font-family-data: ui-monospace, 'SF Mono', Menlo, monospace;
```

| 级别 | 大小 | 字重 | 用途 |
|---|---|---|---|
| 页面标题 | 36rpx | 600 | 导航栏（或系统栏） |
| 卡片标题 | 32rpx | 600 | 单号 |
| 正文 | 28rpx | 400 | 列表、表单 |
| 辅助 | 24rpx | 400 | 时间、提示 |
| 数据 | 28rpx | 500 | `.font-data` 单号/SKU/库位 |

**不加载** Google Fonts / Fira。

---

## Spacing（rpx，750 设计宽）

| Token | 值 | 用途 |
|---|---|---|
| `--space-xs` | 8rpx | 图标与文字间距 |
| `--space-sm` | 16rpx | 卡片内 compact |
| `--space-md` | 24rpx | 表单项间距 |
| `--space-lg` | 32rpx | 卡片 padding |
| `--space-xl` | 48rpx | 区块间距 |
| `--page-gutter` | 32rpx | 页面左右边距 |

---

## TabBar

| 项 | 规范 |
|---|---|
| 高度 | 系统默认 + safe-area-inset-bottom |
| 项数 | 2：待办、我的 |
| 选中色 | `$color-primary` |
| 未选中 | `$color-muted` |
| 图标 | uni-icons 或 SVG，**不用 emoji** |

---

## 组件模式

### 任务卡片（TaskCard）

- 白底、圆角 16rpx、`--shadow-sm`
- 左：类型图标；中：单号 + 状态 Tag；右：箭头
- 整卡可点，pressed 态 opacity 0.85（**不改变布局尺寸**）

### 底部固定 CTA

```scss
.action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
  background: $color-card;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
}
.action-bar__btn {
  height: 96rpx;
  border-radius: 16rpx;
  background: $color-primary;
  color: $color-on-primary;
  font-size: 32rpx;
  font-weight: 600;
}
```

### 数量 Stepper

- 减 | 数字 | 加；按钮 88rpx 见方
- 禁用减到 &lt; 最小单位时

### 库位搜索

- `uni-easyinput` 或原生 input + 候选列表
- 必须从候选选择 `location_id`，**禁止**仅手输文本提交

---

## Motion

- 过渡 150–250ms，`ease-out`
- 不用 scroll reveal / GSAP
- 尊重系统「减少动态效果」

---

## Anti-Patterns

- ❌ Emoji 作为 Tab / 导航图标  
- ❌ 小于 88rpx 的纯图标按钮（无热区扩展）  
- ❌ hover 依赖（小程序用 `:active` / pressed）  
- ❌ 硬编码每页 hex，须走 token  
- ❌ 用「冻结」指盘点锁  
- ❌ 在小程序做审核/创建单据主流程  

---

## Pre-Delivery Checklist（小程序）

- [ ] 主色 / 状态色与 Web 语义一致  
- [ ] 触控目标 ≥ 88rpx  
- [ ] 底部 CTA 不遮挡内容（内容区 padding-bottom）  
- [ ] safe-area 已处理  
- [ ] 写操作带 Idempotency-Key  
- [ ] 403/409 展示后端 message  
- [ ] 下拉刷新可用  
- [ ] 仅 `operator` 可进入作业流  

---

## 页面 Override 索引

| 页面 | 文件 |
|---|---|
| 登录 | [pages/login.md](./pages/login.md) |
| 待办 | [pages/todo.md](./pages/todo.md) |
| 我的 | [pages/my.md](./pages/my.md) |
| 单据详情 | [pages/order-detail.md](./pages/order-detail.md) |
| 上架执行 | [pages/inbound-putaway.md](./pages/inbound-putaway.md) |
| 拣货执行 | [pages/outbound-pick.md](./pages/outbound-pick.md) |
