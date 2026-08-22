# 后端 UAT 人工抽查签字清单

自动化套件：`services/wms-api/tests/uat`（24 用例）。  
发版门禁 CI：**GitHub Actions → wms-api UAT gate**（[workflow](../../.github/workflows/wms-api-uat.yml)）；staging 跑法见 [staging-uat.md](./staging-uat.md)。

本清单**不替代**自动化；未覆盖的验收条目不得只靠签字通过。

发版版本 / 环境：____________________    日期：__________  
自动化 Run（Actions URL 或本地命令输出）：____________________

## 自动化覆盖对照（需求验收标准）

勾选前须已跑通对应 UAT。术语与 `CONTEXT-MAP.md` 一致：盘点锁 ≠ 冻结数量；库存流水 ≠ 操作日志。

| 需求来源 | 验收条目 | 自动化用例 | 覆盖 |
|---|---|---|---|
| platform | 登录成功返回可调用受保护 API 的 Access Token | `test_系统管理员_登录后获得可调用受保护接口的_access_token` | ☐ |
| platform | 无权限用户无法审核单据 | `test_无权限用户无法审核单据` | ☐ |
| platform | 系统管理员可改角色；无权限者不能改角色 | `test_系统管理员_可改用户角色且仓管员无权限改角色` | ☐ |
| platform | 关键操作写入操作日志，且可与流水分别查询 | `test_关键操作写入操作日志且可与库存流水分开查询` | ☐ |
| platform | JSON 写读接口使用统一响应信封 | `test_JSON_写读接口使用统一响应信封` | ☐ |
| catalog | 可创建并启用默认仓库；SKU、库位关联该仓库 | `test_系统管理员_可创建并启用默认仓库及关联SKU库位` | ☐ |
| catalog | 停用 SKU 后不可被新单据选用；历史单据仍可查 | `test_停用SKU后不可被新单据选用且历史单据仍可查` | ☐ |
| catalog | 库位空间状态变更不影响库存冻结数量口径 | `test_库位空间状态变更不影响库存冻结数量口径` | ☐ |
| inbound | 部分上架多次后，行累计、多笔流水、最终在库一致 | `test_仓管员_采购入库多次部分上架后行累计流水与在库一致` | ☐ |
| inbound | 盘点锁库位上架被拒绝 | `test_仓管员_盘点锁库位上架被拒绝` | ☐ |
| inbound | 未上架可取消；已上架取消不得抹掉已入账数量 | `test_仓管员_未上架可取消_已上架取消不抹账` | ☐ |
| outbound | 审核后冻结增加、可用下降 | `test_仓库主管_出库审核完成分配后冻结增加可用下降` | ☐ |
| outbound | 拣货后在库与冻结同减 | `test_仓管员_按库位部分拣货后在库与冻结同减` | ☐ |
| outbound | 部分拣货后取消未拣：预留释放，已实扣不变 | `test_仓库主管_部分拣货后取消未拣正确释放预留且已实扣不抹` | ☐ |
| outbound / inventory | 库存不足时审核（分配）被拒绝，且无负可用/负在库 | `test_仓库主管_库存不足时整单审核被拒绝且无负可用负在库` | ☐ |
| inventory | 两人几乎同时分配同一库存时不超卖 | `test_两人几乎同时分配同一库存不超卖` | ☐ |
| outbound | 盘点锁库位拣货被拒绝 | `test_仓管员_盘点锁库位拣货被拒绝` | ☐ |
| stocktake | 审核前余额不变；审核后余额与流水一致，锁已释放 | `test_仓库主管_发起盘点实盘审核后余额与流水一致并释锁` | ☐ |
| stocktake | 盘点锁期间被锁库位无法上架/拣货 | `test_仓库主管_盘点锁期间上架与拣货均失败释锁后可再上架` | ☐ |
| inventory | 流水可按单据行查询，且与余额变动一致 | `test_流水可按单据行查询且与余额变动一致` | ☐ |
| inventory | 低于安全库存产生预警，回升后解除 | `test_可用量低于安全库存产生预警回升后解除` | ☐ |
| inventory | 上架后库存查询可见余额 | `test_上架后库存查询可见余额` | ☐ |
| overview / platform | 主路径后可拉日报 JSON/CSV（需相应权限） | `test_报表读者_主路径后可拉取日报JSON与CSV` | ☐ |
| overview | 建仓/SKU/库位 → 入库上架 → 库存可见 → 出库分配 → 拣货实扣 → 流水按行可查 | `test_端到端主路径_建仓入库上架库存可见出库分配拣货实扣流水可查` | ☐ |

范围外（不在本签字范围）：Web/小程序 UI、性能压测、备份演练、MVP 外能力。观测缺口见 `services/wms-api/tests/uat/README.md`。

## 按角色抽查（自动化绿灯后）

每角色至少一条关键路径。抽查须用该角色种子账号登录 API（或同等授权），核对与上表自动化条目一致。  
以下步骤假设 API 基址为 `{{BASE}}`（如 `https://staging.example.com`）；先 `POST {{BASE}}/api/v1/auth/login` 取 `access_token`，后续请求带 `Authorization: Bearer <token>`。

### 系统管理员

对照自动化：`test_系统管理员_可改用户角色且仓管员无权限改角色`、`test_无权限用户无法审核单据`。

1. **登录**：`POST /api/v1/auth/login`，body `{"username":"admin","password":"<种子口令>"}` → 200，`data.access_token` 非空。
2. **改角色（应有权）**：`GET /api/v1/users` 找到 `viewer` → `PATCH /api/v1/users/{id}/role`，body `{"role_code":"viewer"}` → 200。
3. **仓管员改角色（应拒绝）**：用 `operator` 登录 → 对同一用户 `PATCH .../role` body `{"role_code":"admin"}` → **403**，信封 `code` ≠ 0。
4. **无权限审核（应拒绝）**：`operator` 创建并提交入库单后，`operator` 或 `viewer` 调用 `POST /api/v1/inbound-orders/{id}/approve` → **403**；`GET` 单据仍为 `pending`。

- 抽查结果：通过 ☐    不通过 ☐    备注：__________
- 签字：__________    日期：__________

### 仓库主管

对照自动化：`test_仓库主管_出库审核完成分配后冻结增加可用下降` 或 `test_仓库主管_发起盘点实盘审核后余额与流水一致并释锁`。

**路径 A — 出库审核（分配）**

1. 确保目标 SKU/库位已有在库（可先跑一条入库上架，或使用 UAT 已建数据）。
2. `operator` 创建出库单并 `submit` → `supervisor` 登录。
3. `POST /api/v1/outbound-orders/{id}/approve`（带 `Idempotency-Key`）→ 200。
4. `viewer` 调用 `GET /api/v1/inventories?warehouse_id=&sku_id=` → 核对 **冻结增加、可用下降**，在库不变。

**路径 B — 盘点审核**

1. `supervisor` 创建盘点单（对某 zone 加盘点锁）→ 录入实盘 → `approve` 调账。
2. `GET /api/v1/inventories/ledgers?ref_line_id=` 与余额一致；释锁后对同库位上架/拣货不再 409。

- 抽查结果：通过 ☐    不通过 ☐    备注：__________
- 签字：__________    日期：__________

### 仓管员

对照自动化：`test_仓管员_采购入库多次部分上架后行累计流水与在库一致` 或 `test_仓管员_按库位部分拣货后在库与冻结同减`。

**路径 A — 部分上架**

1. `operator` 登录；创建采购入库单 → `submit`；由 `supervisor` 审核。
2. `POST /api/v1/inbound-orders/{id}/putaway`（带 `Idempotency-Key`），分两次部分数量上架。
3. `GET` 单据行 `qty_putaway` 累计正确；`GET /api/v1/inventories` 在库与上架量一致。

**路径 B — 拣货实扣**

1. 对已分配出库单，`operator` 调用 `POST /api/v1/outbound-orders/{id}/pick`（带 `Idempotency-Key`）。
2. 核对在库与冻结同减、单据行 `qty_picked` 更新。

- 抽查结果：通过 ☐    不通过 ☐    备注：__________
- 签字：__________    日期：__________

## 发版结论

自动化 `tests/uat`：绿灯 ☐    红灯 ☐    记录：__________

三角色抽查均通过，同意作为业务可上线依据：☐

发版负责人签字：__________    日期：__________
