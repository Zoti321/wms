"""主数据启用状态与库位空间状态（勿与库存冻结数量混淆）。"""

from __future__ import annotations

from enum import IntEnum


class ActiveStatus(IntEnum):
    """主数据生命周期：启用 / 停用。"""

    ACTIVE = 1
    INACTIVE = 0


class LocationSpaceStatus(IntEnum):
    """库位作为空间资源的状态（≠ 库存 qty_frozen）。"""

    IDLE = 1
    OCCUPIED = 2
    FROZEN = 3


SPACE_STATUS_TO_API = {
    LocationSpaceStatus.IDLE: "idle",
    LocationSpaceStatus.OCCUPIED: "occupied",
    LocationSpaceStatus.FROZEN: "frozen",
}

API_TO_SPACE_STATUS = {v: k for k, v in SPACE_STATUS_TO_API.items()}
