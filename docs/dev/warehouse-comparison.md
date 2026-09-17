# WMS 与参考项目 yeqifu/warehouse 对比调研

> 调研日期：2026-09-17  
> 方法：对照 [research skill](../../.claude/skills/research/SKILL.md) — 仅引用 **一手来源**（GitHub 源码/README/SQL、本仓库 SRS 与实现代码），不引用第三方教程。  
> 存放位置：`docs/dev/`（与 [backend-status.md](./backend-status.md) 同属开发态活文档；同类技术调研亦见 [docs/research/web-admin-stack.md](../research/web-admin-stack.md)）。

## 来源索引

| 代号 | 来源 |
|------|------|
| [REF-README] | https://github.com/yeqifu/warehouse/blob/master/README.md |
| [REF-POM] | https://github.com/yeqifu/warehouse/blob/master/pom.xml |
| [REF-SQL] | https://github.com/yeqifu/warehouse/blob/master/warehouse.sql |
| [REF-TREE] | GitHub API `repos/yeqifu/warehouse/git/trees/master?recursive=1` |
| [REF-INPORT] | https://github.com/yeqifu/warehouse/blob/master/src/main/java/com/yeqifu/bus/service/impl/InportServiceImpl.java |
| [REF-REALM] | https://github.com/yeqifu/warehouse/blob/master/src/main/java/com/yeqifu/sys/realm/UserRealm.java |
| [REF-CONST] | https://github.com/yeqifu/warehouse/blob/master/src/main/java/com/yeqifu/sys/common/Constast.java |
| [WMS-README] | 仓库根 [README.md](../../README.md) |
| [WMS-SRS] | [docs/domains/](../domains/README.md) |
| [WMS-SDD] | [docs/dev/](./README.md) |
| [WMS-STATUS] | [backend-status.md](./backend-status.md) |
| [WMS-STACK] | [stack.md](./stack.md) |
| [WMS-PERM] | `services/wms-api/app/platform/domain/permissions.py` |
| [WMS-ROUTES] | `apps/web-admin/src/router/routes.ts` |
| [WMS-MINI] | [mini-program-summary.md](./mini-program-summary.md) |

---

## A. 参考项目：yeqifu/warehouse

### A.1 项目定位与结构

[REF-README] 称系统为「仓库管理系统 warehouse」，分为 **系统模块** 与 **业务模块** 两大块。

[REF-TREE] / [REF-POM] 显示为 **单体 Maven 工程**，无前后端分离仓库：

```
warehouse/
├── pom.xml
├── warehouse.sql          # 全量建表 + 种子数据
└── src/main/
    ├── java/com/yeqifu/
    │   ├── sys/           # 系统：登录、用户、角色、菜单、部门、日志、公告、缓存
    │   └── bus/           # 业务：客户、供应商、商品、进货、退货、销售、销售退货
    └── resources/
        ├── templates/     # Thymeleaf 页面（business/*, system/*）
        └── static/        # LayUI + DTree + 截图资源
```

**架构特征：** Spring Boot 服务端渲染（Thymeleaf）+ LayUI 表格页；REST Controller 主要为 LayUI 的 `DataGridView` 分页接口，**不是** API-first 多端架构 [REF-POM]、[REF-TREE]。

### A.2 功能清单（README + 代码结构）

#### 业务模块 [REF-README]、[REF-TREE]

| 功能 | 说明 | 代码入口 |
|------|------|----------|
| 客户管理 | 列表、分页模糊查、增删改、批量删 | `CustomerController` |
| 供应商管理 | 同上 | `ProviderController` |
| 商品管理 | 列表、分页模糊查、增删改、**图片上传** | `GoodsController`, `FileController` |
| 商品进货 | 进货单 CRUD、退货 | `InportController` |
| 商品退货（对供应商） | 列表、删 | `OutportController` |
| 商品销售 | 销售单 CRUD、销售退货 | `SalesController` |
| 商品销售退货 | 列表、删 | `SalesbackController` |

#### 系统模块 [REF-README]、[REF-TREE]

| 功能 | 说明 | 代码入口 |
|------|------|----------|
| 用户登录 | 用户名/密码/**验证码**；未登录拦截；写登录日志 | `LoginController` |
| 菜单管理 | 树形菜单 CRUD | `MenuController` |
| 角色管理 | 角色 CRUD、**分配权限** | `RoleController`, `PermissionController` |
| 用户管理 | 用户 CRUD、重置密码、**分配角色** | `UserController` |
| 部门管理 | 树形部门 CRUD | `DeptController` |
| 登录日志 | 专用登录审计 | `LoginfoController` |
| 系统公告 | CRUD、批量删 | `NoticeController` |
| 缓存管理 | 管理端 UI（截图见 README） | `CacheController` |

README 预览图还包含权限管理页 [REF-README]，与 `PermissionController` / 菜单-权限树一致。

### A.3 技术栈 [REF-README]、[REF-POM]

| 层级 | 选型 |
|------|------|
| 后端 | Java 8、Spring Boot **2.2.1**、MyBatis-Plus **3.2.0**、Apache Shiro **1.4.0**、Druid、Lombok、Hutool、Fastjson |
| 视图 | Thymeleaf + **LayUI** + **DTree** |
| 数据库 | MySQL（README 写 5.0；SQL 导出为 5.7；驱动 8.0.18） |
| 文档 | Springfox Swagger 2.9.2 |
| 构建/运行 | Maven 3.5.2、Tomcat 8.5（内嵌）、devtools 热部署 |

### A.4 数据与库存模型 [REF-SQL]、[REF-INPORT]

- 商品表 `bus_goods` 含 **`number`（总库存）**、`dangernum`（预警阈值）、`goodsimg` 等字段 [REF-SQL]。
- **无仓库、库区、库位** 维度；库存为 SKU 级单一数量。
- 进货 `InportServiceImpl.save()`：**保存进货记录时直接 `goods.number += 进货数量`**，无单据状态机、无流水表 [REF-INPORT]。
- 同理，销售/退货模块通过改 `bus_goods.number` 实现出入（代码结构对称，见 `bus/` 包）。
- 业务表含 `paytype`（微信/支付宝/银联等）字段 [REF-SQL]。

### A.5 用户、角色与权限 [REF-SQL]、[REF-REALM]、[REF-CONST]

**用户类型**（`sys_user.type`）[REF-CONST]、[REF-SQL]：

| type | 含义 |
|------|------|
| 0 | 超级管理员（`USER_TYPE_SUPER`） |
| 1 | 系统/普通用户 |

**预置角色**（`sys_role`）[REF-SQL]：超级管理员、基础数据管理员、销售管理员、系统管理员、测试。

**授权模型** [REF-REALM]：

- Shiro `AuthorizingRealm`；超级管理员授予 `*:*`。
- 普通用户权限来自 `sys_permission` + `sys_role_permission` + `sys_user_role`。
- 权限实体同时承载 **menu** 与 **permission** 类型 [REF-CONST]（动态菜单 + 接口级权限）。

**组织：** `sys_dept` 树形部门，用户关联 `deptid` [REF-SQL]。

---

## B. 当前 WMS 项目（E:/projects/WMS）

### B.1 项目定位 [WMS-README]、[WMS-SRS]

[WMS-README]：**单据驱动、库存唯一账本、出库软分配** 的 WMS；交付面为 FastAPI 后端、Vue 3 网页后台、uni-app 微信小程序作业端。

[WMS-SRS overview](./overview.md) 目标：账实一致、全程流水追溯、低库存预警、MVP 单仓 8–12 周上线。

### B.2 工程结构 [WMS-SDD repo-layout](./repo-layout.md)

Monorepo：

| 路径 | 职责 |
|------|------|
| `services/wms-api/` | FastAPI 六包：`platform`, `catalog`, `inventory`, `inbound`, `outbound`, `stocktake` |
| `apps/web-admin/` | Vue 3 + Element Plus 管理端 |
| `apps/mini-program/` | uni-app 仓管员上架/拣货 |
| `src/*/CONTEXT.md` | 领域术语（glossary，非代码） |
| `docs/domains/` | 模块化 SRS（权威需求） |

### B.3 功能：已实现 vs 规划

#### 后端 API [WMS-STATUS]

| 阶段 | 状态 |
|------|------|
| M0–M4 | **已完成**（主数据、入出库闭环、盘点、预警、日报、操作日志） |
| M5 上线 | **进行中**（UAT/CI/小程序已交付主路径；压测待） |

已实现路由概览 [WMS-STATUS]：

- **platform**：登录、`/auth/me`、用户、字典、操作日志、日报 JSON/CSV
- **catalog**：仓库、SKU、库位、供应商、客户 CRUD + 停用
- **inventory**：余额、流水、预警（只读 API；写经领域端口）
- **inbound**：入库单全生命周期 + 按行上架
- **outbound**：出库单 + 审核分配 + 拣货实扣 + 取消释放
- **stocktake**：盘点单 + 锁库位 + 盈亏审核

明确 **不在 MVP** [WMS-SRS]、[WMS-STATUS]：Refresh Token、Redis、PDA 扫码、波次拣货、FEFO、多仓调拨、ERP 深度同步、红冲细化。

#### 网页后台 [WMS-ROUTES]

路由已覆盖：工作台、主数据五类、入出库单（列表/新建/编辑/详情）、盘点、库存余额/流水/预警、用户/字典/操作日志/日报 [WMS-ROUTES]。  
E2E 使用 mock API，生产联调见 [WMS-STATUS] 优先级。

#### 小程序 [WMS-MINI]

已交付：operator 登录、待办（待上架/待拣货）、按行上架/拣货、我的。  
**不做**：创建/审核单据、盘点、主数据、扫码 [WMS-MINI]。

### B.4 技术栈 [WMS-STACK]

| 层级 | 选型 |
|------|------|
| 后端 | Python 3.12+、FastAPI、SQLAlchemy 2 同步、MySQL 8、Alembic、JWT（仅 Access） |
| 网页后台 | Vue 3、TS、Vite、Element Plus、Pinia、openapi-typescript |
| 小程序 | uni-app 3、Vue 3、TS |
| 测试/运维 | pytest + httpx、Playwright、Prometheus `/metrics`、`GET /health` |
| MVP 刻意不上 | Redis、Celery |

### B.5 领域模型差异（相对 reference）[WMS-SRS]

| 概念 | WMS |
|------|-----|
| 库存 | **唯一账本** `inventory`；维度：仓库 + SKU + **库位**；可用 = 在库 − 冻结 |
| 入库 | **入库单**状态机；部分上架；记账写**流水** |
| 出库 | 审核 = **软分配（冻结）**；拣货 = 实扣；乐观锁防超卖 |
| 盘点 | **盘点锁**（库位级作业锁，≠ 冻结数量） |
| 销售/进货 | 建模为出库/入库**单据类型**（销售出库、采购入库、退货入库等），非独立 CRUD 模块 |

### B.6 角色与权限 [WMS-SRS]、[WMS-PERM]

[WMS-SRS overview](./overview.md) 业务角色：

| 角色 | 职责 |
|------|------|
| 系统管理员 | 账号、角色、字典 |
| 仓库主管 | 审核、盘点、报表 |
| 仓管员 | 入出库执行；小程序仅上架/拣货 |
| 采购/业务只读 | 库存与单据只读 |

代码中固定四类 `role_code` [WMS-PERM]：`admin`、`supervisor`、`operator`、`viewer`；权限码如 `inbound:approve`、`catalog:write` 等，**矩阵在代码内定义**，无运行时菜单/权限 CRUD API。

---

## C. 差距分析

### C.1 功能对照表

图例：**✓** 已实现 · **△** 部分/等价实现 · **—** 无 · **设计不同** 有意采用不同模型

| 功能域 | yeqifu/warehouse | 仓脉 WMS | 备注 |
|--------|------------------|----------|------|
| **主数据：客户** | ✓ CRUD + 批量删 | ✓ CRUD + 停用 | WMS 软删 [WMS-SRS catalog] |
| **主数据：供应商** | ✓ | ✓ | |
| **主数据：商品/SKU** | ✓ + **图片** + 单字段库存 | ✓ SKU；**无图片**；库存在 inventory 上下文 | [REF-SQL] vs [WMS-SRS] |
| **主数据：仓库/库位** | — | ✓ 仓库→区→位 | WMS 核心能力 |
| **进货/入库** | ✓ 进货单 **即时改库存** | ✓ **入库单** + 审核 + 部分上架 + 流水 | [REF-INPORT] vs [WMS-SRS inbound] |
| **对供应商退货** | ✓ `bus_outport` 独立模块 | △ 可归入「其他出库/退货」类单据 | 无同名独立模块 |
| **销售出库** | ✓ 销售单 **即时扣库存** | ✓ **出库单** + 分配 + 拣货 | 设计不同 |
| **销售退货** | ✓ `bus_salesback` | △ **退货入库** 类型 | 流程更规范 |
| **库存查询** | ✓ 商品 `number` 字段 | ✓ 余额 + **库位分布** + 流水 + 预警 | |
| **库存冻结/预留** | — | ✓ 出库软分配 | WMS 独有 |
| **盘点** | — | ✓ 盘点锁 + 盈亏调账 | WMS 独有 |
| **报表** | —（README 未列） | ✓ 日报 JSON/CSV | [WMS-STATUS] |
| **登录** | ✓ + **验证码** | ✓ JWT，**无验证码** | |
| **用户管理** | ✓ + 头像等 | ✓ 停用/重置密码/改角色 | |
| **角色管理 UI** | ✓ 动态 CRUD + 分配权限 | — 四类角色**代码固定** | [WMS-PERM] |
| **菜单管理 UI** | ✓ 动态树形菜单 | — 前端**静态路由** + `meta.permission` | [WMS-ROUTES] |
| **部门管理** | ✓ 树形 CRUD | — | |
| **权限粒度** | 菜单 + permission 字符串 | 扁平 permission 码 | |
| **登录日志** | ✓ 专用 `sys_loginfo` | △ **操作日志**含登录等敏感操作 | 非专用登录页 |
| **系统公告** | ✓ | — | [REF-TREE] NoticeController |
| **缓存管理** | ✓ 管理 UI | — MVP 无 Redis [WMS-STACK] |
| **支付方式** | ✓ 业务表 `paytype` | — 需求/API 未建模 | [REF-SQL] |
| **批量删除** | ✓ 多模块 | — 主数据为**停用**策略 | |
| **移动端/小程序** | — | ✓ 上架/拣货作业端 | [WMS-MINI] |
| **OpenAPI / 多端 API** | △ Swagger | ✓ 一等 REST + 契约生成 | |
| **幂等 / 防超卖** | — | ✓ Idempotency-Key + 乐观锁 | [WMS-STATUS] |
| **监控运维** | — | ✓ health + Prometheus + runbook | [WMS-STATUS] |
| **自动化 UAT** | — | ✓ 24 条 UAT + CI | [WMS-STATUS] |

### C.2 WMS 有而 warehouse 没有（差异化能力）

1. **多库位库存账本**与流水追溯 [WMS-SRS inventory]
2. **出库软分配 + 拣货实扣** 状态机 [WMS-SRS outbound]
3. **盘点锁**与盈亏调账 [WMS-SRS stocktake]
4. **低库存预警**（安全库存阈值）[WMS-SRS]
5. **微信小程序**仓管作业面 [WMS-MINI]
6. **现代化 Monorepo**（FastAPI + Vue SPA + uni-app）[WMS-STACK]
7. **领域驱动分包**与显式限界上下文 [WMS-SDD]
8. **幂等键、乐观锁、Prometheus、UAT 门禁** [WMS-STATUS]
9. **字典管理**（单位、取消原因等）[WMS-SRS platform]
10. **日报导出** [WMS-STATUS]

### C.3 WMS 相对 warehouse 缺失或较弱项

按「参考项目有、本仓库无或未交付」排序：

| # | 缺失项 | 参考来源 | WMS 现状 | 影响 |
|---|--------|----------|----------|------|
| 1 | **动态角色/权限/菜单管理 UI** | [REF-README] 菜单/角色/权限 | 代码固定矩阵 [WMS-PERM] | 运营无法自助配权，需发版改代码 |
| 2 | **部门/组织架构** | [REF-SQL] `sys_dept` | 无 | 多部门考核、数据隔离时缺口 |
| 3 | **登录验证码** | [REF-README] | 无 |  brute-force 面略大（可依赖网关/WAF） |
| 4 | **专用登录日志页** | [REF-README] 登录日志 | 操作日志合并 [WMS-SRS platform] | 审计查询需过滤 |
| 5 | **系统公告** | [REF-README]、[REF-TREE] | 无 | 库内通知/停机预告 |
| 6 | **商品/SKU 图片** | [REF-README] 商品图片上传 | catalog 无 image 字段 | 现场识别商品不便 |
| 7 | **支付方式** | [REF-SQL] `paytype` | 未建模 | 若需财务对账需扩展 |
| 8 | **缓存管理界面** | [REF-README] | MVP 无 Redis [WMS-STACK] | 不适用当前架构；二期若上 Redis 再议 |
| 9 | **「即时改库存」简化录入** | [REF-INPORT] | 必须走单据 | 小作坊式快速录入不如 reference 轻 |
| 10 | **批量物理删除** | [REF-README] 各模块 batch delete | 仅停用 [WMS-SRS] | 有意设计；非功能回退 |

另：**性能压测** [WMS-STATUS]、**Web 与真实 API 全量联调** [WMS-STATUS] 为 WMS 自身 M5 缺口，reference 亦未提供。

### C.4 优先级建议

| 优先级 | 建议 | 理由 |
|--------|------|------|
| **P0（M5 内）** | 完成 Web Admin 与真实 API 联调、staging UAT、压测基线 | [WMS-STATUS] 已列 M5 阻塞项 |
| **P1（MVP+ / 运营）** | SKU 图片（对象存储 + catalog 字段）；登录验证码（可选） | 贴近 reference 商品管理与安全基线 |
| **P2（若组织扩大）** | 可配置 RBAC（角色/权限 CRUD API + 管理页） | 对标 reference 角色/权限/菜单，但建议保留 permission 码与后端 `require_permissions` 对齐 |
| **P2** | 系统公告（只读广播 + 管理 CRUD） | 对标 reference notice，实现轻 |
| **P3** | 部门维度（用户挂 dept_id，报表按部门） | 仅在有组织隔离需求时 |
| **P3** | 单据行「支付方式/结算方式」扩展字段 | 财务场景；reference 有但较浅 |
| **不建议照搬** | 进货/销售即时改 `goods.number` | 与 WMS 账本/流水/防超卖核心设计冲突 [WMS-SRS] |
| **不建议照搬** | LayUI 单体 + Shiro 菜单树 | 与 ADR-0001/0003 技术栈决策相反 [WMS-STACK] |

---

## D. README 结构对照与 WMS 改写建议

### D.1 reference README 结构 [REF-README]

| 章节 | 内容 |
|------|------|
| 系统名称 | 一级标题 |
| 系统概要 | 一段话 + 模块划分 |
| 功能模块 | **深度嵌套列表**（业务 / 系统 × 子功能 × 操作点） |
| 技术选型 | 后台 / 前台分表 |
| 开发环境 | OS、语言、IDE、构建、服务器、DB、托管 |
| 预览效果 | **大量截图**（登录、各管理页、业务页） |
| 讨论 | Issue + 联系方式 |

**未包含：** Badge、License、Quick Start 命令、目录树、文档链接。

### D.2 当前 WMS README [WMS-README]

极简：**一句话定位** + **快速开始表格**（链到 docs / 各子项目 README）+ **Monorepo 一行结构**。

### D.3 建议 WMS README 章节（按实际状态）

| 建议章节 | 是否采纳 reference 模式 | 说明 |
|----------|-------------------------|------|
| **产品一句话 + 架构图** | 概要 ✓，截图可选 | 强调「单据驱动 + 三交付面」；可用 mermaid 替代 reference 式 prose |
| **功能矩阵** | 功能模块 ✓（改表格） | 列：模块 / Web / API / 小程序 / 状态；链到 [domains](../domains/README.md) |
| **技术栈** | 技术选型 ✓ | 精简表 + 链 [stack.md](./stack.md)；**不要**复制 Java/LayUI |
| **快速开始** | reference **缺**；WMS **应保留并扩展** | 前置：Docker、uv、pnpm；三行命令启动 api / web / 小程序 |
| **角色说明** | reference implicit | 四角色表 [WMS-SRS overview](../domains/overview.md) |
| **文档入口** | WMS 优势 | `docs/index.html`、`docs/dev/`、`AGENTS.md` |
| **截图/GIF** | 预览效果 ✓（M5 后） | Web 工作台 + 小程序待办；放 `docs/assets/` |
| **CI / 质量** | reference 无 | Badge：test、UAT（若公开 CI） |
| **贡献/Issue** | 讨论 ✓（去掉 QQ 有偿讲解） | 链 GitHub Issues |
| **License** | 两项目均需确认 | 若开源则标明 |

**不宜照搬：** reference 的嵌套 bullet 逐操作点罗列（WMS 已有 SRS）；reference 联系方式；Tomcat/Maven 环境列表。

---

## 附录：参考项目 Controller 与表一览

**业务 Controller** [REF-TREE]：`Customer`, `Provider`, `Goods`, `Inport`, `Outport`, `Sales`, `Salesback`, `Business`, `File`

**系统 Controller** [REF-TREE]：`Login`, `User`, `Role`, `Permission`, `Menu`, `Dept`, `Loginfo`, `Notice`, `Cache`, `System`

**业务表** [REF-SQL]：`bus_customer`, `bus_provider`, `bus_goods`, `bus_inport`, `bus_outport`, `bus_sales`, `bus_salesback`

**系统表** [REF-SQL]：`sys_user`, `sys_role`, `sys_permission`, `sys_role_permission`, `sys_user_role`, `sys_dept`, `sys_loginfo`, `sys_notice`
