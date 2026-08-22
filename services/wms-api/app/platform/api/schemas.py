"""认证相关请求/响应 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeData(BaseModel):
    id: int
    username: str
    role_code: str
    permissions: list[str]


class AssignRoleRequest(BaseModel):
    role_code: str = Field(min_length=1, max_length=64)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    role_code: str = Field(min_length=1, max_length=64)


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class CreateDictItemRequest(BaseModel):
    dict_type: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sort_order: int = Field(default=0, ge=0)


class UpdateDictItemRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    sort_order: int | None = Field(default=None, ge=0)


class DailyReportData(BaseModel):
    """UTC 业务日经营汇总（只读；库存快照为查询时刻当前值）。"""

    warehouse_id: int
    business_date: str = Field(description="UTC 业务日 YYYY-MM-DD")
    inbound_order_count: int = Field(description="当日有上架记录的入库单数")
    putaway_qty: str = Field(description="当日上架量合计（三位小数）")
    outbound_order_count: int = Field(description="当日有拣货记录的出库单数")
    picked_qty: str = Field(description="当日实扣（拣货）量合计（三位小数）")
    sku_count: int = Field(description="当前有货（qty_on_hand>0）的 SKU 数")
    total_available: str = Field(description="当前总可用 qty_on_hand−qty_frozen")
    open_alert_count: int = Field(description="当前有效库存预警条数")
