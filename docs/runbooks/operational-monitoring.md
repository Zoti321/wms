# 运行监控与告警 Runbook（dev / staging / prod）

> 适用：`services/wms-api` 暴露的 Prometheus 指标。与 **库存预警**（业务 API `GET /api/v1/inventories/alerts`）无关。

## 与 `/health` 的分工

| 能力 | 端点 | 用途 |
|------|------|------|
| **摘流探活** | `GET /health` | DB 不可达 → HTTP **503** + `degraded`；负载均衡据此摘掉实例 |
| **运行监控** | `GET /metrics` | 错误率、耗时、连接池、库存写路径失败计数；供 Prometheus 趋势告警 |

恢复实例后：先确认 `/health` 200，再观察 `/metrics` 中 5xx 率与 `wms_inventory_operation_total` 15–30 分钟（参见 [MySQL 备份与恢复 Runbook](./mysql-backup-restore.md) §观察期）。

## 安全

- **`/metrics` 无需 JWT**，与 `/health` 相同；**禁止公网暴露**，仅内网/VPC 抓取。
- 指标标签不含用户 PII；路由使用模板路径（非原始 URL），控制 cardinality。
- 应急关闭：`METRICS_ENABLED=false` → `/metrics` 返回 404。

## 配置

| 变量 | 默认 | 说明 |
|------|------|------|
| `METRICS_ENABLED` | 非 `test` 环境为 `true` | 设为 `false` 关闭指标端点 |
| `APP_ENV=test` | — | 测试默认关闭，避免 CI 依赖 Prometheus |

## Prometheus 抓取示例

```yaml
scrape_configs:
  - job_name: wms-api
    metrics_path: /metrics
    scrape_interval: 15s
    static_configs:
      - targets: ["wms-api:8000"]
```

## 主要指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `wms_http_requests_total` | Counter | HTTP 请求量（method / handler / status）；不含 `/health`、`/metrics` |
| `wms_http_request_duration_seconds` | Histogram | 接口耗时 |
| `wms_db_pool_*` | Gauge | 连接池 size / checked_in / checked_out / overflow |
| `wms_inventory_operation_total` | Counter | 库存记账：operation=`allocate|pick|release|adjust`，result=`success|insufficient|conflict|error` |

## Cardinality 注意

- 勿在高基数 path 上打标签；instrumentator 已忽略 untemplated 路由。
- 业务 counter 仅 4×4 标签组合，可安全聚合。

## 告警规则

示例见 [`docs/ops/prometheus-alerts.example.yml`](../ops/prometheus-alerts.example.yml)。阈值需按 staging 压测后调整。

## 本地验证

```bash
cd services/wms-api
METRICS_ENABLED=true uv run uvicorn app.main:app --app-dir .
curl -s http://127.0.0.1:8000/metrics | head
```

## 相关

- Issue #15
- ADR-0002：Prometheus Pull
- [健康检查 / 备份 Runbook](./mysql-backup-restore.md)
