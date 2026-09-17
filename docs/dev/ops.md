# 部署与运维要点

- 环境：dev / staging / prod 隔离；密钥走环境变量
- 数据库每日备份；恢复演练至少每季度一次（步骤见 [MySQL 备份与恢复 Runbook](../runbooks/mysql-backup-restore.md)）
- 健康检查：`GET /health` 返回 JSON（`status` + `checks.database`）；DB 不可达时 HTTP 503 + `degraded`，便于负载均衡摘流；本地无库可设 `HEALTH_CHECK_DB=false`
- 监控：API 错误率、接口耗时、分配/实扣失败率、连接池；Prometheus 见 [运行监控 Runbook](../runbooks/operational-monitoring.md)
- 上线检查清单：迁移脚本、回滚方案、默认仓库种子数据、初始管理员
