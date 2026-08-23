# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** 仓脉 WMS
**Generated:** 2026-08-22 22:28:25
**Category:** Enterprise WMS / Logistics Operations Admin
**Stack:** Vue 3 + TypeScript + Vite + Element Plus + Pinia
**Design Dials:** Variance 3/10 (Centered / Minimal) | Motion 3/10 (Subtle) | Density 8/10 (Dense / Dashboard)

---

## Global Rules

### Design Principles

1. **效率优先**：列表/表单是主界面；减少装饰，缩短操作路径（≤3 次点击完成常见任务）。
2. **数据可扫读**：表格行高 36–40px；状态用颜色 + 文字标签；数字右对齐、等宽字体。
3. **状态语义一致**：全系统共用入库/出库/库存/盘点状态色，禁止各模块自定义。
4. **权限可见性**：无权限的按钮/菜单不展示（`v-permission`），而非点击后报错。
5. **默认浅色、可选深色**：仓内办公环境以浅色为主；深色供夜间值班场景。

### Color Palette — Light (Default)

| Role | Hex | CSS Variable | Element Plus Token |
|------|-----|--------------|-------------------|
| Primary | `#1E40AF` | `--color-primary` | `--el-color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` | — |
| Secondary | `#475569` | `--color-secondary` | — |
| Accent / Success | `#16A34A` | `--color-success` | `--el-color-success` |
| Warning | `#D97706` | `--color-warning` | `--el-color-warning` |
| Danger | `#DC2626` | `--color-danger` | `--el-color-danger` |
| Info | `#0284C7` | `--color-info` | `--el-color-info` |
| Background | `#F1F5F9` | `--color-background` | page bg |
| Surface / Card | `#FFFFFF` | `--color-card` | `--el-bg-color` |
| Foreground | `#0F172A` | `--color-foreground` | `--el-text-color-primary` |
| Muted Foreground | `#64748B` | `--color-muted-foreground` | `--el-text-color-secondary` |
| Border | `#E2E8F0` | `--color-border` | `--el-border-color-light` |

### Color Palette — Dark (Optional)

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#3B82F6` | `--color-primary` |
| Background | `#0F172A` | `--color-background` |
| Surface / Card | `#1E293B` | `--color-card` |
| Foreground | `#F8FAFC` | `--color-foreground` |
| Muted Foreground | `#94A3B8` | `--color-muted-foreground` |
| Border | `#334155` | `--color-border` |

### WMS Status Semantics

| Domain | Status | Color Token | Tag Style |
|--------|--------|-------------|-----------|
| 入库 | 草稿 / 待上架 / 已完成 / 已取消 | info / warning / success / default | `el-tag` |
| 出库 | 草稿 / 待审核 / 拣货中 / 已出库 / 已取消 | default / warning / primary / success / info | `el-tag` |
| 库存 | 正常 / 低于安全库存 / 冻结 / 盘点锁 | success / warning / danger / info | `el-tag` + 图标 |
| 盘点 | 进行中 / 待审核 / 已生效 | primary / warning / success | `el-tag` |

**Color Notes:** 业务状态色独立于品牌主色；红/绿不单靠颜色，须配文字标签。

### Typography

- **Heading Font:** Fira Sans（600–700）
- **Body Font:** Fira Sans（400–500）
- **Data / Code Font:** Fira Code（单号、SKU、库位编码、数量列）
- **Mood:** 专业、精确、数据密集、低干扰
- **Scale:** 12px 辅助 · 14px 正文/表格 · 16px 小标题 · 20px 页面标题

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap');
```

**Element Plus 覆盖：**
```css
:root {
  --el-font-family: 'Fira Sans', system-ui, sans-serif;
  --el-font-size-base: 14px;
}
.font-data { font-family: 'Fira Code', monospace; }
```

### Spacing Variables

*Density: 8/10 — Dense / Dashboard*

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `2px` / `0.125rem` | Tight gaps |
| `--space-sm` | `4px` / `0.25rem` | Icon gaps, inline spacing |
| `--space-md` | `8px` / `0.5rem` | Standard padding |
| `--space-lg` | `12px` / `0.75rem` | Section padding |
| `--space-xl` | `16px` / `1rem` | Large gaps |
| `--space-2xl` | `24px` / `1.5rem` | Section margins |
| `--space-3xl` | `32px` / `2rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Layout & Information Architecture

### Shell（AdminLayout）

```
┌──────────┬─────────────────────────────────────────────┐
│ Sidebar  │ Header: 面包屑 + 页面标题    用户 | 退出   │
│ 220px    ├─────────────────────────────────────────────┤
│ 可折叠   │ Main: 筛选栏 → 工具栏 → 内容区（表格/表单）  │
│          │                                             │
└──────────┴─────────────────────────────────────────────┘
```

| Token | Value | Usage |
|-------|-------|-------|
| `--sidebar-width` | `220px` | 展开宽度 |
| `--sidebar-collapsed` | `64px` | 折叠仅图标 |
| `--header-height` | `56px` | 顶栏 |
| `--content-padding` | `16px` | 主内容区内边距 |
| `--grid-gap` | `8px` | KPI 卡片网格间距 |

**导航分组：** 工作台 · 主数据 · 入库 · 出库 · 库存 · 盘点 · 系统（二期）

**图标库：** `@element-plus/icons-vue`（与 Element Plus 一致）；菜单项必配图标 + 文字。

### Page Patterns

| 页面类型 | 结构 | 关键组件 |
|---------|------|---------|
| 列表页 | 筛选 → 操作栏 → 表格 → 分页 | `el-form` inline · `el-table` · `el-pagination` |
| 详情页 | 摘要卡片 → Tab/分段 → 明细表格 | `el-descriptions` · `el-tabs` |
| 表单页 | 分组 fieldset → 底部固定操作栏 | `el-form` label-top · `el-affix` |
| 工作台 | KPI 行 → 待办列表 → 快捷入口 | `el-row`/`el-col` · Bullet Chart |
| 登录 | 居中卡片 · 品牌 + 表单 | `el-card` · 无侧边栏 |

### Tables（Data-Dense）

- 行高：`36px`（紧凑）/ `40px`（默认）
- 表头：`sticky` + 浅灰背景 `#F8FAFC`
- 数字列：右对齐 + `.font-data`
- 状态列：`el-tag` size="small"
- 操作列：文字按钮 link 类型，主操作在左
- 空态：`el-empty` + 引导 CTA（如「新建入库单」）
- 移动端：`overflow-x-auto` 包裹，不撑破布局

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #22C55E;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #1E293B;
  border: 2px solid #1E293B;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #0F172A;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #1E293B;
  outline: none;
  box-shadow: 0 0 0 3px #1E293B20;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Minimalism & Swiss Style

**Keywords:** Clean, simple, spacious, functional, white space, high contrast, geometric, sans-serif, grid-based, essential

**Best For:** Enterprise apps, dashboards, documentation sites, SaaS platforms, professional tools

**Key Effects:** Subtle hover (200-250ms), smooth transitions, sharp shadows if any, clear type hierarchy, fast loading

### Page Pattern

**Pattern Name:** Real-Time / Operations Landing

- **Conversion Strategy:** Offer a demo or sandbox and show trust signals. Label telemetry as live only when backed by a current source, with update time and stale state. Provide pause/hide or update-frequency controls for tickers and previews, stop offscreen/hidden work, support keyboard controls, and render a static final snapshot under reduced motion.
- **CTA Placement:** Primary CTA in nav + After metrics
- **Section Order:** Hero (product + live preview or status) > Key metrics/indicators > How it works > CTA (Start trial / Contact)

---

## Motion

**Scroll Reveal** (Subtle) — Trigger: scroll (viewport enter) | Duration: 300-400ms | Easing: `power1.out`

```js
gsap.from(el, { opacity: 0, y: 12, duration: 0.35, ease: 'power1.out', scrollTrigger: { trigger: el, start: 'top 90%', toggleActions: 'play none none reverse' } });
```

**Framework notes:** Requires the ScrollTrigger plugin registered once via gsap.registerPlugin(ScrollTrigger); Use matchMedia('(prefers-reduced-motion: reduce)') to skip non-essential motion and render the final state immediately

- ✅ Keep the y offset small (8-16px) so it reads as a fade, not a slide
- ❌ Don't reveal below-the-fold content needed for SEO/crawlers as invisible-by-default without a no-JS fallback
- ⚡ toggleActions 'play none none reverse' avoids re-triggering on every scroll direction change

---

## Anti-Patterns (Do NOT Use)

- ❌ Slow updates
- ❌ No automation

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile
