# 鉴权与角色门禁

## 登录流程

```
登录页 → POST /auth/login → 存 access_token
      → GET /auth/me → 校验 role_code
      → operator：进入 Tab·待办
      → 其他角色：无权空态（仅可退出）
```

### API

| 步骤 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 登录 | POST | `/api/v1/auth/login` | Body: `{ username, password }` |
| 当前用户 | GET | `/api/v1/auth/me` | 返回 `id`, `username`, `role_code`, `permissions` |

响应信封：`{ code, message, data, traceId }`，`code === 0` 为成功（与 web-admin 一致）。

登录成功 `data` 含 `access_token`、`token_type`（`bearer`）。

## Token 持久化

| 项 | 值 |
|---|---|
| Storage Key | `wms_access_token` |
| 读写 | `uni.getStorageSync` / `uni.setStorageSync` |
| 请求头 | `Authorization: Bearer <token>` |
| 清除时机 | 主动退出；`code === 40100` 或 HTTP 401 |

对标实现：`apps/web-admin/src/utils/tokenStorage.ts`。

## 角色门禁（MVP 硬规则）

作业端**仅面向仓管员**，登录成功后检查：

```ts
user.role_code === 'operator'
```

| role_code | 中文 | 登录后 |
|---|---|---|
| `operator` | 仓管员 | 进入待办 Tab |
| `supervisor` | 仓库主管 | **无权使用作业端** 空态 |
| `admin` | 系统管理员 | 同上 |
| `viewer` | 只读用户 | 同上 |

依据：`services/wms-api/app/platform/domain/permissions.py` 中 `ROLE_OPERATOR` 对应需求里的「仓管员」。

> 主管/管理员的审核、报表、盘点等能力仅在 **Web Admin** 提供；避免双端职责重叠。

### 无权空态

- 标题：「无权使用作业端」
- 说明：「请使用网页后台，或联系管理员分配仓管员账号。」
- 唯一操作：退出登录

## 权限与 API

小程序 MVP **不实现**按钮级 `v-permission`；依赖：

1. 登录门禁（仅 `operator`）
2. 后端 `require_permissions`（上架需 `inbound:write`，拣货需 `outbound:write`）

`operator` 已具备上述写权限；若后端返回 403，用 `uni.showToast` 展示 `message`。

## 会话策略

- MVP **无 Refresh Token**（与后端 ADR-0001 一致）
- Token 过期 → 401 → 清 Token → 跳转登录页
- 不实现「记住密码」；依赖 storage 中的 Token 减少重复登录

## 开发种子账号

与 web-admin / API README 一致（如 `operator` / 开发密码）。**勿在文档或代码库提交生产密码。**

## 安全要点

- 仅 HTTPS 生产环境
- 登录页禁止截图敏感信息日志
- 密码字段使用 `password` 类型；允许粘贴（无障碍）
