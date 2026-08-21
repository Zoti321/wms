"""盘点请求 DTO。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class StocktakeOrderCreate(BaseModel):
    warehouse_id: int
    zone: str | None = Field(default=None, max_length=32)
    remark: str | None = Field(default=None, max_length=255)
    order_no: str | None = Field(default=None, max_length=64)


class CountLineInput(BaseModel):
    line_id: int
    counted_qty: Decimal = Field(ge=0)


class RecordCountsRequest(BaseModel):
    lines: list[CountLineInput] = Field(min_length=1)
