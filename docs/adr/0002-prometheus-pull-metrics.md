# MVP：Prometheus Pull 运行监控

仓脉 WMS 后端在 M5 通过 `GET /metrics` 暴露 Prometheus 文本格式指标，由外部 Prometheus/Alertmanager 拉取与告警。MVP 不上 Pushgateway、不引入 OpenTelemetry Collector，与应用内 **库存预警**（安全库存业务事实）严格分离——后者走 `GET /api/v1/inventories/alerts`，不走 Prometheus。

理由：与 #14 健康检查运维路径一致；staging 单机可跑；符合 ADR-0001（无 Redis/队列）。若日后需要分布式追踪，可另引入 OTel，但不替代 Pull 指标。
