#!/usr/bin/env bash
set -euo pipefail

# 开发环境：启动 MySQL + 迁移 + FastAPI（http://localhost:8000）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

require_command uv

if [[ -z "${WMS_API_PORT:-}" ]]; then
  resolve_api_port
fi

start_mysql

api_dir="${WMS_REPO_ROOT}/services/wms-api"
cd "${api_dir}"

if [[ ! -f .env ]]; then
  log "创建 .env（来自 .env.example）"
  cp .env.example .env
fi

log "同步 Python 依赖..."
uv sync

log "执行数据库迁移..."
uv run alembic upgrade head

log "启动 API（http://localhost:${WMS_API_PORT}，Swagger: /docs）..."
exec uv run uvicorn app.main:app --reload --app-dir . --port "${WMS_API_PORT}"
