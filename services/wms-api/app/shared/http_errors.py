"""HTTP adapter：domain 异常 → 统一 envelope；写操作幂等头校验。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.shared.response import fail


@dataclass(frozen=True)
class DomainErrorRule:
    """单条 domain 异常 → HTTP 语义映射（子类规则须排在基类之前）。"""

    exc_type: type[Exception]
    code: int
    http_status: int
    default_message: str = ""


def map_domain_error(exc: Exception, rules: Sequence[DomainErrorRule]) -> None:
    """将 domain 异常映射为 HTTPException（detail 为 fail 包络）；未知异常原样抛出。"""
    for rule in rules:
        if isinstance(exc, rule.exc_type):
            message = str(exc)
            if not message:
                message = rule.default_message
            body, _ = fail(
                code=rule.code, message=message, http_status=rule.http_status
            )
            raise HTTPException(status_code=rule.http_status, detail=body) from exc
    raise exc


def require_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    """FastAPI Depends：写操作必须携带 Idempotency-Key。"""
    if not idempotency_key:
        body_fail, _ = fail(
            code=40000, message="缺少 Idempotency-Key", http_status=400
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail
        )
    return idempotency_key
