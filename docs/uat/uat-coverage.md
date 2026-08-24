# 后端 UAT：需求 ↔ 自动化追溯

发版/上线门禁以 **`services/wms-api/tests/uat`** 自动化套件为准；24 用例全绿即视为后端验收通过，**无需人工签字**。

- 套件说明：[`services/wms-api/tests/uat/README.md`](../../services/wms-api/tests/uat/README.md)
- Staging 重跑：[`staging-uat.md`](./staging-uat.md)
- CI：**push `main` / PR（`services/wms-api`）** 跑 [`wms-api-test.yml`](../../.github/workflows/wms-api-test.yml)；对 staging 可手动触发 [`wms-api-uat.yml`](../../.github/workflows/wms-api-uat.yml) 并填写 `uat_base_url`

术语与 `CONTEXT-MAP.md` 一致：**盘点锁** ≠ 冻结数量；**库存流水** ≠ 操作日志。

## 覆盖对照

| 需求来源 | 验收条目 | 自动化用例 |
|---|---|---|
| platform | 登录成功返回可调用受保护 API 的 Access Token | `test_系统管理员_登录后获得可调用受保护接口的_access_token` |
| platform | 无权限用户无法审核单据 | `test_无权限用户无法审核单据` |
| platform | 系统管理员可改角色；无权限者不能改角色 | `test_系统管理员_可改用户角色且仓管员无权限改角色` |
| platform | 关键操作写入操作日志，且可与流水分别查询 | `test_关键操作写入操作日志且可与库存流水分开查询` |
| platform | JSON 写读接口使用统一响应信封 | `test_JSON_写读接口使用统一响应信封` |
| catalog | 可创建并启用默认仓库；SKU、库位关联该仓库 | `test_系统管理员_可创建并启用默认仓库及关联SKU库位` |
| catalog | 停用 SKU 后不可被新单据选用；历史单据仍可查 | `test_停用SKU后不可被新单据选用且历史单据仍可查` |
| catalog | 库位空间状态变更不影响库存冻结数量口径 | `test_库位空间状态变更不影响库存冻结数量口径` |
| inbound | 部分上架多次后，行累计、多笔流水、最终在库一致 | `test_仓管员_采购入库多次部分上架后行累计流水与在库一致` |
| inbound | 盘点锁库位上架被拒绝 | `test_仓管员_盘点锁库位上架被拒绝` |
| inbound | 未上架可取消；已上架取消不得抹掉已入账数量 | `test_仓管员_未上架可取消_已上架取消不抹账` |
| outbound | 审核后冻结增加、可用下降 | `test_仓库主管_出库审核完成分配后冻结增加可用下降` |
| outbound | 拣货后在库与冻结同减 | `test_仓管员_按库位部分拣货后在库与冻结同减` |
| outbound | 部分拣货后取消未拣：预留释放，已实扣不变 | `test_仓库主管_部分拣货后取消未拣正确释放预留且已实扣不抹` |
| outbound / inventory | 库存不足时审核（分配）被拒绝，且无负可用/负在库 | `test_仓库主管_库存不足时整单审核被拒绝且无负可用负在库` |
| inventory | 两人几乎同时分配同一库存时不超卖 | `test_两人几乎同时分配同一库存不超卖` |
| outbound | 盘点锁库位拣货被拒绝 | `test_仓管员_盘点锁库位拣货被拒绝` |
| stocktake | 审核前余额不变；审核后余额与流水一致，锁已释放 | `test_仓库主管_发起盘点实盘审核后余额与流水一致并释锁` |
| stocktake | 盘点锁期间被锁库位无法上架/拣货 | `test_仓库主管_盘点锁期间上架与拣货均失败释锁后可再上架` |
| inventory | 流水可按单据行查询，且与余额变动一致 | `test_流水可按单据行查询且与余额变动一致` |
| inventory | 低于安全库存产生预警，回升后解除 | `test_可用量低于安全库存产生预警回升后解除` |
| inventory | 上架后库存查询可见余额 | `test_上架后库存查询可见余额` |
| overview / platform | 主路径后可拉日报 JSON/CSV（需相应权限） | `test_报表读者_主路径后可拉取日报JSON与CSV` |
| overview | 建仓/SKU/库位 → 入库上架 → 库存可见 → 出库分配 → 拣货实扣 → 流水按行可查 | `test_端到端主路径_建仓入库上架库存可见出库分配拣货实扣流水可查` |

原「三角色人工抽查」路径已由上表中带 `admin` / `supervisor` / `operator` 的用例覆盖，不再单独执行。

## 范围外

Web/小程序 UI、性能压测、备份演练、MVP 外能力不在本套件范围。观测缺口见 [`services/wms-api/tests/uat/README.md`](../../services/wms-api/tests/uat/README.md#观测缺口)。

## 本地运行

```bash
cd services/wms-api
uv run pytest tests/uat -v --fail-on-skipped
```

对 staging：

```bash
export UAT_BASE_URL="https://staging.example.com"
uv run pytest tests/uat -v --fail-on-skipped
```
