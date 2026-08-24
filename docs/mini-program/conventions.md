# 开发规范与术语

## 领域术语（必须遵守）

与 [`CONTEXT-MAP.md`](../../CONTEXT-MAP.md) 一致；**禁止**在 UI 或代码注释中使用模糊别名。

| 正确 | 错误 / 禁止 |
|---|---|
| 上架 | 「入库完成」指整单 |
| 拣货、实扣 | 与「分配（预留）」混称 |
| 分配（预留） | 小程序 MVP 不涉及，文档勿写「审核=实扣」 |
| 盘点锁 | 与「冻结数量」混称 |
| 库存流水 | 与「操作日志」混称 |

## 代码命名

| 类别 | 约定 | 示例 |
|---|---|---|
| 页面目录 | kebab 或与业务域一致 | `pages/inbound/putaway.vue` |
| 组件 | PascalCase 文件名 | `TaskCard.vue` |
| API 模块 | 与 web-admin 对齐 | `inboundOrders.ts` |
| Store | `useAuthStore`、`useAppStore` | 同 web-admin |
| 常量 | `INBOUND_STATUS_LABEL` | 复制自 web `labels.ts` 或抽 shared（二期） |

## 状态文案与颜色

状态中文与 Tag 语义 **必须与 web-admin 一致**：

- 来源：`apps/web-admin/src/constants/labels.ts`
- 小程序用 `uni-tag` 或自定义 Tag，颜色 token 见 `MASTER-MINI.md` 的「WMS 状态语义」

## 时间展示

- API / DB：**UTC**
- 展示：转本地时区（可用 `dayjs` 或轻量 formatter，与 web 格式统一为 `YYYY-MM-DD HH:mm`）

## 数量展示

- 使用字符串或 Decimal 友好格式，避免 JS 浮点误差
- 列表/表单中的 SKU 编码、单号、库位编码使用 `.font-data`（等宽）

## Git 与提交

- 提交信息：**简体中文**，说明「为什么」
- 分支：`feature/mini-*`

## 测试

| 类型 | 范围 |
|---|---|
| 单元 | `api/client` 信封解析、幂等键、labels |
| 类型 | `pnpm typecheck:mini-program` |
| E2E | 二期；M5 以前依赖后端 UAT + 人工微信开发者工具走查 |

## Agent 加载顺序

1. `docs/mini-program/README.md`
2. 任务相关模块 md（本目录）
3. `design-system/wms/MASTER-MINI.md` + 目标页 `pages/*.md`
4. 若动到业务规则：`docs/requirements/inbound.md` 或 `outbound.md` + 对应 `CONTEXT.md`

## 明确不做（MVP）

- 扫码（相机 / 硬件扫码头）
- 创建、审核、取消单据
- 盘点、库存查询、报表
- 多仓切换 UI
- 深色模式
- 离线提交队列
