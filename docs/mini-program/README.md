# 小程序开发文档（给 Agent / 开发者）

仓脉 WMS **仓管员作业端**（uni-app · 微信小程序）的实现说明。业务规则见 [`docs/requirements/`](../requirements/README.md)；术语见 [`CONTEXT-MAP.md`](../../CONTEXT-MAP.md)；后端契约见 [`docs/development.html`](../development.html)。

**UI / UX 设计**不在此目录重复：全局规范见 [`design-system/wms/MASTER-MINI.md`](../../design-system/wms/MASTER-MINI.md)；各页 override 见 [`design-system/wms/pages/`](../../design-system/wms/pages/)。

## 产品定位（M5 MVP）

| 做 | 不做 |
|---|---|
| 登录（仅 `operator` 仓管员） | 创建 / 审核入库单、出库单 |
| 待办：待上架入库单、待拣货出库单 | 盘点实盘、主数据维护、报表 |
| 按行 **上架**、按行 **拣货（实扣）** | PDA 扫码（二期） |
| 调与 web-admin 相同的 FastAPI | 离线队列、Refresh Token |

## 何时读哪个文件

| 任务涉及… | 先读 |
|---|---|
| 目录结构、路由、Tab、Pinia、uni-ui | [architecture.md](./architecture.md) |
| 登录、Token、角色门禁 | [auth.md](./auth.md) |
| `uni.request`、OpenAPI 类型、信封、幂等 | [api-client.md](./api-client.md) |
| 页面流、路由表、API 映射 | [pages.md](./pages.md) |
| 术语、命名、与 Web 差异 | [conventions.md](./conventions.md) |
| 某页布局 / 交互 / 视觉 | `design-system/wms/pages/<page>.md` + `MASTER-MINI.md` |

接任务时：**overview 级约束 + 本目录 1～2 个模块 + 对应页面 design override**，不要默认通读全部。

## 模块列表

1. [architecture.md](./architecture.md) — 工程与架构  
2. [auth.md](./auth.md) — 鉴权与门禁  
3. [api-client.md](./api-client.md) — API 客户端  
4. [pages.md](./pages.md) — 页面与数据流  
5. [conventions.md](./conventions.md) — 规范与术语  

## 快速链接

- 本地开发：[`apps/mini-program/README.md`](../../apps/mini-program/README.md)  
- Web 后台对标：[`apps/web-admin/README.md`](../../apps/web-admin/README.md)  
- OpenAPI 快照：`apps/mini-program/openapi.snapshot.json`（与 web-admin 同步；生成见 [api-client.md](./api-client.md)）  
- 权限矩阵：`services/wms-api/app/platform/domain/permissions.py`
