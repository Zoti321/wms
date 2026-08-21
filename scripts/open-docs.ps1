# 快速打开仓脉 WMS 文档总览（docs/index.html）
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$indexPath = Join-Path $repoRoot "docs\index.html"

if (-not (Test-Path -LiteralPath $indexPath)) {
    Write-Error "未找到总览文档: $indexPath"
    exit 1
}

Start-Process -FilePath $indexPath
