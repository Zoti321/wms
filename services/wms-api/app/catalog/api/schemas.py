"""主数据请求/响应 DTO。"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class WarehouseData(BaseModel):
    id: int
    warehouse_code: str
    name: str
    status: int


class SkuCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=16)
    spec: str | None = Field(default=None, max_length=128)
    barcode: str | None = Field(default=None, max_length=64)
    safety_stock: Decimal = Field(default=Decimal("0"), ge=0)


class SkuUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=16)
    spec: str | None = Field(default=None, max_length=128)
    barcode: str | None = Field(default=None, max_length=64)
    safety_stock: Decimal | None = Field(default=None, ge=0)


class SkuData(BaseModel):
    id: int
    sku_code: str
    name: str
    unit: str
    spec: str | None
    barcode: str | None
    safety_stock: str
    status: int


class LocationCreate(BaseModel):
    warehouse_id: int
    location_code: str = Field(min_length=1, max_length=64)
    zone: str | None = Field(default=None, max_length=32)
    aisle: str | None = Field(default=None, max_length=32)
    bin: str | None = Field(default=None, max_length=32)
    space_status: Literal["idle", "occupied", "frozen"] = "idle"


class LocationUpdate(BaseModel):
    zone: str | None = Field(default=None, max_length=32)
    aisle: str | None = Field(default=None, max_length=32)
    bin: str | None = Field(default=None, max_length=32)
    space_status: Literal["idle", "occupied", "frozen"] | None = None


class LocationData(BaseModel):
    id: int
    warehouse_id: int
    location_code: str
    zone: str | None
    aisle: str | None
    bin: str | None
    space_status: Literal["idle", "occupied", "frozen"]
    status: int


class SupplierCreate(BaseModel):
    supplier_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class SupplierData(BaseModel):
    id: int
    supplier_code: str
    name: str
    status: int


class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class CustomerData(BaseModel):
    id: int
    customer_code: str
    name: str
    status: int
