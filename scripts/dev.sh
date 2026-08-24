#!/usr/bin/env bash
set -euo pipefail

# 开发环境：同时启动后端 API 与网页后台

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pids=()

cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]}"; do
    if kill -0 "${pid}" 2>/dev/null; then
      kill -TERM "${pid}" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

# shellcheck source=lib/common.sh
source "${script_dir}/lib/common.sh"

resolve_api_port

log "同时启动后端与网页后台"
log "  API:       http://localhost:${WMS_API_PORT}"
log "  Web Admin: http://localhost:5173"
log "按 Ctrl+C 停止全部服务"

bash "${script_dir}/dev-api.sh" &
pids+=($!)

bash "${script_dir}/dev-web-admin.sh" &
pids+=($!)

wait -n
exit_code=$?
cleanup
exit "${exit_code}"
