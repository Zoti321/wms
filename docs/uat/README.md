# 后端 UAT 交付物索引

Issue #9 交付：独立 API 黑盒验收套件 + 发版门禁 + 按角色人工签字。

## 自动化

| 项 | 位置 |
|---|---|
| UAT 套件（24 用例） | [`services/wms-api/tests/uat/`](../../services/wms-api/tests/uat/) |
| 套件说明与观测缺口 | [`services/wms-api/tests/uat/README.md`](../../services/wms-api/tests/uat/README.md) |
| 日常 PR 集成测 | [`services/wms-api/tests/`](../../services/wms-api/tests/)（不含 `uat/`） |

本地跑 UAT（需 MySQL，或设 `UAT_BASE_URL` 对 staging）：

```bash
cd services/wms-api
uv run pytest tests/uat
```

## CI 门禁

| 流水线 | 触发 | 范围 |
|---|---|---|
| [wms-api-test.yml](../../.github/workflows/wms-api-test.yml) | PR / push `main` | 日常集成测，**不含** UAT |
| [wms-api-uat.yml](../../.github/workflows/wms-api-uat.yml) | **手动** `workflow_dispatch` | 发版前 UAT 必过 |

发版负责人在 GitHub Actions 选择 **wms-api UAT gate** 运行；可选填写 `uat_base_url` 对 staging 重跑同一剧本。

## 人工签字

自动化绿灯后，三角色各抽查一条关键路径：

- 清单与 API 步骤：[`backend-signoff.md`](./backend-signoff.md)
- Staging 前提与变量：[`staging-uat.md`](./staging-uat.md)

签字完成后由发版负责人在 Issue #9 评论并关闭。

## 术语

与 `CONTEXT-MAP.md` 一致：**盘点锁** ≠ 冻结数量；**库存流水** ≠ 操作日志。
