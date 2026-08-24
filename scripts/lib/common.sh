#!/usr/bin/env bash

_wms_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WMS_REPO_ROOT="$(cd "${_wms_lib_dir}/../.." && pwd)"

log() {
  echo "[dev] $*"
}

die() {
  echo "[dev] $*" >&2
  exit 1
}

require_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "未找到命令: ${cmd}"
}

_run_python() {
  if command -v python >/dev/null 2>&1; then
    python "$@"
    return 0
  fi
  if command -v py >/dev/null 2>&1; then
    py -3 "$@"
    return 0
  fi
  return 1
}

resolve_api_port() {
  local script="${_wms_lib_dir}/resolve_api_port.py"
  local requested="${WMS_API_PORT:-}"
  local port

  if [[ -n "${requested}" ]]; then
    port="$(_run_python "${script}" "${requested}")" || port=""
  else
    port="$(_run_python "${script}")" || port=""
  fi

  if [[ -z "${port}" ]]; then
    die "无法解析 API 端口（需要 python 或 py）；可手动设置 WMS_API_PORT"
  fi

  export WMS_API_PORT="${port}"

  if [[ -z "${requested}" && "${port}" != "8000" ]]; then
    log "端口 8000 不可用（常见于 Windows Hyper-V 保留端口），API 改用 ${port}"
  fi
}

start_mysql() {
  require_command docker

  log "启动 MySQL（docker compose）..."
  (
    cd "${WMS_REPO_ROOT}"
    if docker compose up --help 2>/dev/null | grep -q -- '--wait'; then
      docker compose up -d --wait mysql
    else
      docker compose up -d mysql
      local attempt=1
      while (( attempt <= 30 )); do
        if docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -proot --silent 2>/dev/null; then
          return 0
        fi
        sleep 2
        (( attempt++ ))
      done
      die "MySQL 未在预期时间内就绪"
    fi
  )
}
