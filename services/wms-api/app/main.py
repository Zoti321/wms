"""仓脉 WMS API 入口。"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 确保 Alembic / 元数据能发现模型
import app.catalog.infrastructure.models  # noqa: F401
import app.inbound.infrastructure.models  # noqa: F401
import app.inventory.infrastructure.lock_models  # noqa: F401
import app.inventory.infrastructure.models  # noqa: F401
import app.outbound.infrastructure.models  # noqa: F401
import app.platform.infrastructure.models  # noqa: F401
import app.stocktake.infrastructure.models  # noqa: F401
from app.catalog.api.router import router as catalog_router
from app.inbound.api.router import router as inbound_router
from app.inventory.api.router import router as inventory_router
from app.outbound.api.router import router as outbound_router
from app.platform.api.auth import router as auth_router
from app.shared.config import get_settings
from app.stocktake.api.router import router as stocktake_router

OPENAPI_DESCRIPTION = """
仓脉 WMS HTTP API（OpenAPI 3，FastAPI 自动生成）。

## 在 Swagger UI 中试调

1. 调用 `POST /api/v1/auth/login`，使用开发种子账号拿到 `access_token`
2. 点击右上角 **Authorize**，值填入 token（无需手写 `Bearer ` 前缀；若 UI 要求完整头则用 `Bearer <token>`）
3. 再调用受保护接口；入库上架、出库审核/拣货/取消、盘点创建/审核/取消等写操作还需请求头 `Idempotency-Key`

生产环境（`APP_ENV=prod`/`production`）不暴露本页、`/redoc` 与 `/openapi.json`。
""".strip()

OPENAPI_TAGS = [
    {"name": "auth", "description": "登录与当前操作者"},
    {"name": "catalog", "description": "主数据：仓库 / SKU / 库位 / 供应商 / 客户"},
    {"name": "inventory", "description": "库存余额、流水与预警查询（数量账唯一所有者）"},
    {"name": "inbound", "description": "入库单：提交、审核、上架、取消"},
    {"name": "outbound", "description": "出库单：审核分配、拣货实扣、取消释放预留"},
    {"name": "stocktake", "description": "盘点单：加锁、实盘、审核调账、取消释锁"},
]


def create_app() -> FastAPI:
    settings = get_settings()
    docs_enabled = not settings.is_production
    application = FastAPI(
        title="仓脉 WMS API",
        version="0.1.0",
        description=OPENAPI_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        message = exc.detail if isinstance(exc.detail, str) else "请求失败"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code * 100,
                "message": message,
                "data": None,
                "traceId": uuid.uuid4().hex,
            },
        )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(catalog_router, prefix="/api/v1")
    application.include_router(inventory_router, prefix="/api/v1")
    application.include_router(inbound_router, prefix="/api/v1")
    application.include_router(outbound_router, prefix="/api/v1")
    application.include_router(stocktake_router, prefix="/api/v1")
    return application


app = create_app()
