"""运行监控：Prometheus 指标暴露（issue #15）。"""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import REGISTRY, Counter, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.requests import Request
from starlette.responses import Response

from app.shared.config import Settings

_EXCLUDED_HANDLERS = (
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
)

_LATENCY_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

inventory_operation_total = Counter(
    "wms_inventory_operation_total",
    "Inventory ledger mutations by operation and result",
    ["operation", "result"],
)

wms_db_pool_size = Gauge("wms_db_pool_size", "SQLAlchemy connection pool configured size")
wms_db_pool_checked_in = Gauge(
    "wms_db_pool_checked_in", "Connections currently idle in the pool"
)
wms_db_pool_checked_out = Gauge(
    "wms_db_pool_checked_out", "Connections currently checked out from the pool"
)
wms_db_pool_overflow = Gauge(
    "wms_db_pool_overflow", "Overflow connections currently in use"
)


def record_inventory_operation(operation: str, result: str) -> None:
    inventory_operation_total.labels(operation=operation, result=result).inc()


def _refresh_pool_gauges() -> None:
    try:
        from app.shared.db import get_engine

        pool = get_engine().pool
    except Exception:
        return
    wms_db_pool_size.set(pool.size())
    wms_db_pool_checked_in.set(pool.checkedin())
    wms_db_pool_checked_out.set(pool.checkedout())
    wms_db_pool_overflow.set(pool.overflow())


async def metrics_endpoint(_request: Request) -> Response:
    _refresh_pool_gauges()
    payload = generate_latest(REGISTRY)
    return Response(content=payload, media_type="text/plain; version=0.0.4; charset=utf-8")


def setup_metrics(application: FastAPI, settings: Settings) -> None:
    """注册 HTTP 中间件与 /metrics；未启用时不暴露端点。"""
    if not settings.metrics_enabled:
        return

    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=list(_EXCLUDED_HANDLERS),
    ).instrument(
        application,
        metric_namespace="wms",
        metric_subsystem="http",
        latency_highr_buckets=_LATENCY_BUCKETS,
    ).add()

    @application.get("/metrics", include_in_schema=False)
    async def metrics(_request: Request) -> Response:
        return await metrics_endpoint(_request)
