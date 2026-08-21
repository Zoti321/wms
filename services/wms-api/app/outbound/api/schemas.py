"""出库请求/响应 DTO。"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OutboundLineInput(BaseModel):
    sku_id: int
    planned_qty: Decimal = Field(gt=0)


class OutboundOrderCreate(BaseModel):
    warehouse_id: int
    order_type: Literal["sales", "material", "other"]
    lines: list[OutboundLineInput] = Field(min_length=1)
    customer_id: int | None = None
    remark: str | None = Field(default=None, max_length=255)
    order_no: str | None = Field(default=None, max_length=64)


class OutboundOrderUpdate(BaseModel):
    lines: list[OutboundLineInput] | None = None
    customer_id: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class AllocationInput(BaseModel):
    line_id: int
    location_id: int


class ApproveRequest(BaseModel):
    allocations: list[AllocationInput] = Field(min_length=1)


class PickRequest(BaseModel):
    line_id: int
    location_id: int
    qty: Decimal = Field(gt=0)
