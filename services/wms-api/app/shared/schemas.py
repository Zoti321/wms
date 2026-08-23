"""跨模块共享请求体。"""

from __future__ import annotations

from pydantic import BaseModel


class CancelRequest(BaseModel):
    cancel_reason_code: str | None = None
