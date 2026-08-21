# wms-api

仓脉 WMS 后端（FastAPI + MySQL 8.0 + uv）。领域包与 `src/*/CONTEXT.md` 对齐：`catalog` / `inventory` / `inbound` / `outbound` / `stocktake`；`platform` 为身份与操作日志。

## 本地启动

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --app-dir .
```

健康检查：`GET /health`
