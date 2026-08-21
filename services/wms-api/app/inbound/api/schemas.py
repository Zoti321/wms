"""入库请求/响应 DTO。"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class InboundLineInput(BaseModel):
    sku_id: int
    planned_qty: Decimal = Field(gt=0)


class InboundOrderCreate(BaseModel):
    warehouse_id: int
    order_type: Literal["purchase", "return", "other"]
    lines: list[InboundLineInput] = Field(min_length=1)
    supplier_id: int | None = None
    remark: str | None = Field(default=None, max_length=255)
    order_no: str | None = Field(default=None, max_length=64)


class InboundOrderUpdate(BaseModel):
    lines: list[InboundLineInput] | None = None
    supplier_id: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class PutawayRequest(BaseModel):
    line_id: int
    location_id: int
    qty: Decimal = Field(gt=0)
