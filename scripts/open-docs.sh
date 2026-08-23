#!/usr/bin/env bash
set -euo pipefail

# 快速打开仓脉 WMS 文档总览（docs/index.html）

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
index_path="${script_dir}/../docs/index.html"

if [[ ! -f "$index_path" ]]; then
  echo "未找到总览文档: $index_path" >&2
  exit 1
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$index_path"
elif command -v open >/dev/null 2>&1; then
  open "$index_path"
elif command -v cygpath >/dev/null 2>&1; then
  explorer "$(cygpath -w "$index_path")"
elif command -v wslpath >/dev/null 2>&1; then
  cmd.exe /c start "" "$(wslpath -w "$index_path")"
else
  echo "无法自动打开浏览器，请手动访问: $index_path" >&2
  exit 1
fi
