"""仓脉 WMS API 入口。"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 确保 Alembic / 元数据能发现模型
import app.catalog.infrastructure.models  # noqa: F401
import app.inbound.infrastructure.models  # noqa: F401
import app.inventory.infrastructure.models  # noqa: F401
import app.platform.infrastructure.models  # noqa: F401
from app.catalog.api.router import router as catalog_router
from app.inbound.api.router import router as inbound_router
from app.inventory.api.router import router as inventory_router
from app.platform.api.auth import router as auth_router
from app.shared.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="仓脉 WMS API", version="0.1.0")

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
    return application


app = create_app()
