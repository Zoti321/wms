"""HTTP 错误映射 deep module：domain exc → 统一 envelope。"""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.shared.http_errors import DomainErrorRule, map_domain_error, require_idempotency_key


class _BaseDomainError(Exception):
    pass


class _NotFound(_BaseDomainError):
    pass


class _Conflict(_BaseDomainError):
    pass


_RULES = (
    DomainErrorRule(_NotFound, 40400, status.HTTP_404_NOT_FOUND, "资源不存在"),
    DomainErrorRule(_Conflict, 40900, status.HTTP_409_CONFLICT, "冲突"),
    DomainErrorRule(_BaseDomainError, 40000, status.HTTP_400_BAD_REQUEST),
)


def test_map_domain_error_not_found_uses_default_message() -> None:
    with pytest.raises(HTTPException) as raised:
        map_domain_error(_NotFound(), _RULES)
    assert raised.value.status_code == 404
    assert raised.value.detail["code"] == 40400
    assert raised.value.detail["message"] == "资源不存在"


def test_map_domain_error_uses_exc_message_when_present() -> None:
    with pytest.raises(HTTPException) as raised:
        map_domain_error(_Conflict("SKU 已占用"), _RULES)
    assert raised.value.detail["message"] == "SKU 已占用"


def test_map_domain_error_re_raises_unknown() -> None:
    with pytest.raises(ValueError, match="boom"):
        map_domain_error(ValueError("boom"), _RULES)


def test_map_domain_error_empty_message_without_default() -> None:
    with pytest.raises(HTTPException) as raised:
        map_domain_error(_BaseDomainError(), _RULES)
    assert raised.value.detail["message"] == ""


def test_require_idempotency_key_rejects_missing() -> None:
    with pytest.raises(HTTPException) as raised:
        require_idempotency_key(None)
    assert raised.value.status_code == 400
    assert raised.value.detail["message"] == "缺少 Idempotency-Key"


def test_require_idempotency_key_returns_value() -> None:
    assert require_idempotency_key("abc-123") == "abc-123"
