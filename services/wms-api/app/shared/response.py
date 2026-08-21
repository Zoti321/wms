"""统一 API 响应包络。"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex, alias="traceId")

    model_config = {"populate_by_name": True}


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return ApiResponse(code=0, message=message, data=data).model_dump(by_alias=True)


def fail(
    *,
    code: int = 40100,
    message: str,
    data: Any = None,
    http_status: int = 401,
) -> tuple[dict[str, Any], int]:
    body = ApiResponse(code=code, message=message, data=data).model_dump(by_alias=True)
    return body, http_status
