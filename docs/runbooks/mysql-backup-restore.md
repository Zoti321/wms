# MySQL 备份与恢复 Runbook（dev / staging）

> 适用环境：本地 Docker Compose、staging 单机 MySQL。生产按同一流程扩展，密钥与保留策略由运维单独维护。

## 健康检查与摘流约定

`GET /health` 无需认证，返回结构化 JSON：

| 场景 | HTTP | 响应示例 |
|------|------|----------|
| DB 可达 | 200 | `{"status":"ok","checks":{"database":"ok"}}` |
| DB 不可达 | **503** | `{"status":"degraded","checks":{"database":"fail"}}` |
| 跳过 DB 检查 | 200 | `{"status":"ok","checks":{"database":"skipped"}}` |

- 负载均衡 / 编排：以 **HTTP 503** 判定实例不可服务并摘流。
- 本地无 MySQL、仅需验证进程：设置 `HEALTH_CHECK_DB=false`（见 `.env.example`）。
- DB 探测：`SELECT 1`，超时默认 2s（`HEALTH_CHECK_DB_TIMEOUT_SECONDS`）。

## 备份策略（dev / staging 口径）

| 项 | 建议 |
|----|------|
| 频率 | 每日至少一次逻辑备份 |
| 保留 | dev 7 天；staging 14 天（按磁盘调整） |
| 内容 | 全库 `mysqldump` + 校验文件大小/行数 |
| 存储 | 勿与 MySQL 数据卷同盘；staging 建议对象存储或备份主机 |

## 前置条件

- 已知连接参数（Compose 默认：`wms` / `wms`，库 `wms`，root `root`）。
- 备份目录存在且可写，例如 `./backups/`（勿提交进 Git）。

## 每日备份

### A. Docker Compose（推荐 dev）

在仓库根目录，MySQL 容器名默认 `wms-mysql`：

```bash
mkdir -p backups
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
docker exec wms-mysql mysqldump \
  -uroot -proot \
  --single-transaction \
  --routines \
  --triggers \
  --set-gmt-time \
  --default-character-set=utf8mb4 \
  wms > "backups/wms-${STAMP}.sql"
gzip "backups/wms-${STAMP}.sql"
ls -lh "backups/wms-${STAMP}.sql.gz"
```

### B. 直连主机 MySQL（staging / 本机非容器）

```bash
mkdir -p backups
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mysqldump \
  -h 127.0.0.1 -P 3306 -u wms -p \
  --single-transaction \
  --routines \
  --triggers \
  --set-gmt-time \
  --default-character-set=utf8mb4 \
  wms > "backups/wms-${STAMP}.sql"
gzip "backups/wms-${STAMP}.sql.gz"
```

### 备份后快速验证

```bash
gzip -t "backups/wms-${STAMP}.sql.gz"
# 可选：查看头部是否含 CREATE TABLE
zcat "backups/wms-${STAMP}.sql.gz" | head -n 30
```

## 恢复步骤

> **警告**：恢复会覆盖目标库数据。先在隔离库或 staging 演练，确认后再动生产。

### 1. 停止写入（staging）

- 摘流 API 实例，或暂停依赖写库的作业。
- 确认无进行中的入库/出库/盘点写操作。

### 2. 恢复到空库 / 覆盖库

**Docker Compose：**

```bash
BACKUP=backups/wms-YYYYMMDDTHHMMSSZ.sql.gz   # 替换为实际文件
gunzip -c "$BACKUP" | docker exec -i wms-mysql mysql -uroot -proot wms
```

**直连：**

```bash
gunzip -c "$BACKUP" | mysql -h 127.0.0.1 -P 3306 -u wms -p wms
```

若需先建空库：

```sql
DROP DATABASE IF EXISTS wms;
CREATE DATABASE wms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 迁移版本对齐

备份已含表结构时通常无需再跑迁移；若恢复的是**空库 + 仅数据**或版本不确定：

```bash
cd services/wms-api
uv run alembic upgrade head
```

### 4. 恢复后验证清单

- [ ] `GET /health` 返回 200 且 `checks.database` 为 `ok`
- [ ] `POST /api/v1/auth/login` 种子/业务账号可登录
- [ ] 抽查主数据：`GET /api/v1/warehouses` 有预期记录
- [ ] 抽查库存：`GET /api/v1/inventories` 与恢复前抽样一致
- [ ] 操作日志 / 最近单据 ID 连续性与业务方确认
- [ ] 恢复耗时与 RTO 记录在演练纪要中

### 5. 恢复 API 流量

- 确认 health 200 后重新加入负载均衡。
- 观察错误率与慢查询 15–30 分钟。

## 季度演练记录模板

| 字段 | 内容 |
|------|------|
| 日期 | |
| 环境 | dev / staging |
| 备份文件 | 路径 + SHA256 |
| 执行人 | |
| 恢复耗时 | 开始 / 结束 |
| 验证项 | 勾选 §「恢复后验证清单」 |
| 问题与改进 | |

## 相关配置

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | API 连接串 |
| `HEALTH_CHECK_DB` | `true`（默认）探测 DB；`false` 本地无库跳过 |
| `HEALTH_CHECK_DB_TIMEOUT_SECONDS` | DB 探测超时（默认 2） |

## 不在本 Runbook 范围

- 生产自动备份 Cron / 异地复制（由运维平台单独落地）
- Prometheus / Grafana 接入
- 全链路压测
