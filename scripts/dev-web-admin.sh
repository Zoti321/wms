#!/usr/bin/env bash
set -euo pipefail

# 开发环境：启动网页后台 Vite（http://localhost:5173，API 代理至 :8000）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

require_command pnpm

apps_dir="${WMS_REPO_ROOT}/apps"
cd "${apps_dir}"

if [[ ! -d node_modules ]]; then
  log "安装前端依赖..."
  pnpm install
fi

log "启动网页后台（http://localhost:5173）..."
exec pnpm dev:web-admin
