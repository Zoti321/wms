# 小程序作业端（M5）

仓管员**上架 / 拣货**作业面，与 web-admin 共用 FastAPI。业务规则见 [inbound.md](../requirements/inbound.md)、[outbound.md](../requirements/outbound.md)；实现细则见 [`docs/mini-program/`](../mini-program/README.md)；UI 见 `design-system/wms/MASTER-MINI.md` 与各页 `pages/*.md`。

## 进度（权威）

| 项 | 状态 |
|----|------|
| 功能主路径（登录 / 待办 / 入库上架 / 出库拣货 / 我的） | 已交付（源码 + Vitest；见 #32） |
| OpenAPI 类型 | 已落地：`generate:api` → `src/types/openapi.d.ts`，参与 typecheck |
| CI 门禁 | 已纳入：`mini-program-test.yml`（path filter → typecheck + unit test） |
| 微信开发者工具人工走查 | 见下方清单；关闭 #33 前须由人勾选必过项 |

明确不做（不阻塞 M5 作业面完成判据）：uni-ui/组件抽取、待办 `pendingLineCount`、PDA 扫码、离线、Refresh Token、微信 E2E 自动化等（见 #33 Out of Scope）。

## 定位与范围

| 做 | 不做（MVP） |
|----|------------|
| 登录（仅 `operator` 仓管员） | 创建 / 审核入出库单 |
| 待办：待上架入库单、待拣货出库单 | 盘点、主数据、报表、扫码 |
| 按行上架、按行拣货（实扣） | 离线队列、Refresh Token |

## 技术栈

| 项 | 选型 |
|----|------|
| 框架 | uni-app 3 + Vue 3 + TypeScript + Vite（`apps/mini-program/`） |
| 平台 | 微信小程序（H5 仅开发预览） |
| UI | uni-ui + SCSS token（`MASTER-MINI.md`） |
| 状态 | Pinia；JWT 存 `uni.storage` |
| API | `uni.request`；OpenAPI 类型独立生成；写操作 `Idempotency-Key` |

## 路由与 Tab

- **TabBar**：待办 · 我的
- **栈页**：登录、入库/出库详情、上架/拣货执行
- 待办数据：并行拉取 `inbound-orders`（`approved`+`putaway`）与 `outbound-orders`（`approved`+`picking`），客户端合并排序

## 文档索引

| 文档 | 路径 |
|------|------|
| 开发文档地图 | `docs/mini-program/README.md` |
| 架构 / 鉴权 / API / 页面 / 规范 | `docs/mini-program/*.md` |
| 小程序设计 Master | `design-system/wms/MASTER-MINI.md` |
| 页面 UI override | `design-system/wms/pages/{login,todo,my,order-detail,inbound-putaway,outbound-pick}.md` |
| 本地 README | `apps/mini-program/README.md` |

## 人工走查清单（微信开发者工具，必过）

基础库 ≥ 2.19.2；对真实或 UAT API。Agent 不能代替勾选；全部必过项通过后关闭 #33。

- ☐ operator 登录成功并进入待办
- ☐ 非 operator 见无权空态且可回到登录
- ☐ 待办展示待上架入库与待拣货出库；筛选全部/入库/出库可用；下拉刷新可用
- ☐ 入库详情 → 上架：选库位、提交数量、成功返回详情且数量更新
- ☐ 出库详情 → 拣货：分配库位只读、提交实扣、成功返回详情且数量更新
- ☐ 我的展示用户/角色/仓库只读信息；退出回到登录
- ☐ 写操作失败（如盘点锁或校验错误）有提示且不导致无法重试的空白态

（可选）☐ 网络断开提示、☐ 幂等重试不重复记账——有环境则测，不阻塞关闭。
