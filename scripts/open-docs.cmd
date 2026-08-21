@echo off
REM 快速打开仓脉 WMS 文档总览（docs/index.html）
set "DOC=%~dp0..\docs\index.html"
if not exist "%DOC%" (
  echo 未找到总览文档: %DOC%
  exit /b 1
)
start "" "%DOC%"
