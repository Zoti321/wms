# API 客户端

## 基址

```ts
function resolveApiBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL?.trim() ?? ''
  return base ? `${base.replace(/\/$/, '')}/api/v1` : '/api/v1'
}
```

- **H5**：留空 `VITE_API_BASE_URL`，由 Vite dev server 代理
- **微信小程序**：必填完整 API 根；不走浏览器 CORS

## 信封与错误

与 web-admin 相同：

```ts
interface ApiEnvelope<T> {
  code: number
  message: string
  data: T | null
  traceId: string
}
```

| 场景 | 处理 |
|---|---|
| `code !== 0` | 抛业务错误，展示 `message` |
| `code === 40100` 或 HTTP 401 | 清 Token，跳转登录 |
| 网络失败 | `uni.showToast`「网络异常，请重试」 |

对标：`apps/web-admin/src/api/client.ts`、`apps/web-admin/src/types/api.ts`。

## OpenAPI 类型生成

小程序**独立**维护类型，不 import web-admin 源码。

```bash
# 在 apps/ 目录：先刷新 web-admin 快照，再同步到小程序并生成类型
pnpm --filter web-admin generate:openapi-snapshot
cp web-admin/openapi.snapshot.json mini-program/openapi.snapshot.json
pnpm --filter mini-program generate:api
```

产物：`apps/mini-program/src/types/openapi.d.ts`（纳入 git；`pnpm --filter mini-program typecheck` 会消费）。  
`src/types/api.ts` 对 OpenAPI 已建模的请求体（`LoginRequest` / `PutawayRequest` / `PickRequest`）做薄 re-export；列表/详情等 data 载荷因后端未声明 `response_model`，仍手写并对齐 web-admin。

作业端 MVP 实际用到的 schema：

- `LoginRequest`、`PutawayRequest`、`PickRequest`（来自生成类型）
- 列表/详情 order 类型（手写，与 web `types/api.ts` 字段对齐）

## 请求封装要点

使用 `uni.request` 包装为 Promise，并：

1. 注入 `Authorization`
2. 解析 JSON 信封
3. 写操作附加 `Idempotency-Key` header

```ts
uni.request({
  url: `${baseUrl}/inbound-orders/${orderId}/putaway`,
  method: 'POST',
  header: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    'Idempotency-Key': idempotencyKey,
  },
  data: { line_id, location_id, qty },
})
```

## 幂等键（Idempotency-Key）

写操作：**上架**、**拣货** 必须带此头。

策略（与 web-admin 一致）：

1. 用户打开执行页 / 改字段前：生成新 UUID（`createIdempotencyKey()`）
2. 同一表单多次点「确认」：**复用同一 key** 直至成功或用户修改 line/库位/数量
3. 修改任一字段后：生成新 key

对标：`apps/web-admin/src/utils/idempotency.ts`。

## 分页

列表接口统一 `page`、`page_size`。常量 `MAX_LIST_PAGE_SIZE = 100` 与后端一致（`apps/mini-program/src/constants/api.ts`）。

待办合并列表时，每类单据建议 `page_size=50`，按 `updated_at` 降序。

## 作业端用到的 API 清单

| 用途 | 方法 | 路径 | 权限 |
|---|---|---|---|
| 登录 | POST | `/auth/login` | 公开 |
| 当前用户 | GET | `/auth/me` | 已登录 |
| 待办·入库 | GET | `/inbound-orders?status=approved` 与 `?status=putaway` | `inbound:read` |
| 待办·出库 | GET | `/outbound-orders?status=approved` 与 `?status=picking` | `outbound:read` |
| 入库详情 | GET | `/inbound-orders/{id}` | `inbound:read` |
| 出库详情 | GET | `/outbound-orders/{id}` | `outbound:read` |
| 库位搜索 | GET | `/locations?warehouse_id=&code=` | `catalog:read` |
| 上架 | POST | `/inbound-orders/{id}/putaway` | `inbound:write` + Idempotency-Key |
| 拣货 | POST | `/outbound-orders/{id}/pick` | `outbound:write` + Idempotency-Key |

> 列表 API 的 `status` 为**单值** query；待办需并行请求 `approved` 与 `putaway`（或 `picking`）后客户端合并。二期可增 `/work/tasks` 聚合接口。

### 写操作 Body

**PutawayRequest / PickRequest**（结构相同）：

```json
{
  "line_id": 1,
  "location_id": 10,
  "qty": "5"
}
```

`qty` 为大于 0 的数或十进制字符串。

## 典型错误

| 场景 | 预期 |
|---|---|
| 盘点锁库位 | HTTP 409，`message` 含盘点/锁相关文案 |
| 库存不足（拣货） | 409 / 业务 code，展示后端 message |
| 乐观锁冲突 | 提示重试，刷新详情后重新提交 |
| 重复幂等键 | 后端返回首次结果，前端视为成功 |

## 在线策略

MVP **无离线队列**。失败仅 toast + 页内重试；不缓存未提交的写操作。
