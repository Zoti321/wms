"""健康检查：进程存活与可选 MySQL 连通性探测。"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.shared.config import Settings, get_settings


def probe_database(database_url: str, timeout_seconds: float) -> bool:
    """轻量 SELECT 1；失败或超时返回 False。"""
    timeout = max(1, int(timeout_seconds))
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": timeout, "read_timeout": timeout},
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, OSError):
        return False
    finally:
        engine.dispose()


def build_health_response(
    settings: Settings | None = None,
) -> tuple[dict[str, object], int]:
    """返回 (JSON 体, HTTP 状态码)。"""
    cfg = settings or get_settings()
    checks: dict[str, str] = {}

    if not cfg.health_check_db:
        checks["database"] = "skipped"
        return {"status": "ok", "checks": checks}, 200

    if probe_database(cfg.database_url, cfg.health_check_db_timeout_seconds):
        checks["database"] = "ok"
        return {"status": "ok", "checks": checks}, 200

    checks["database"] = "fail"
    return {"status": "degraded", "checks": checks}, 503
