"""角色权限矩阵：JWT role_code → 权限码。"""

from __future__ import annotations

ROLE_ADMIN = "admin"
ROLE_SUPERVISOR = "supervisor"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"

PERM_CATALOG_READ = "catalog:read"
PERM_CATALOG_WRITE = "catalog:write"
PERM_INBOUND_READ = "inbound:read"
PERM_INBOUND_WRITE = "inbound:write"
PERM_INBOUND_APPROVE = "inbound:approve"
PERM_OUTBOUND_READ = "outbound:read"
PERM_OUTBOUND_WRITE = "outbound:write"
PERM_OUTBOUND_APPROVE = "outbound:approve"
PERM_STOCKTAKE_READ = "stocktake:read"
PERM_STOCKTAKE_WRITE = "stocktake:write"
PERM_STOCKTAKE_APPROVE = "stocktake:approve"
PERM_INVENTORY_READ = "inventory:read"
PERM_AUDIT_READ = "audit:read"
PERM_DICT_READ = "dict:read"
PERM_DICT_WRITE = "dict:write"
PERM_USER_WRITE = "user:write"
PERM_REPORT_READ = "report:read"

_ALL = frozenset(
    {
        PERM_CATALOG_READ,
        PERM_CATALOG_WRITE,
        PERM_INBOUND_READ,
        PERM_INBOUND_WRITE,
        PERM_INBOUND_APPROVE,
        PERM_OUTBOUND_READ,
        PERM_OUTBOUND_WRITE,
        PERM_OUTBOUND_APPROVE,
        PERM_STOCKTAKE_READ,
        PERM_STOCKTAKE_WRITE,
        PERM_STOCKTAKE_APPROVE,
        PERM_INVENTORY_READ,
        PERM_AUDIT_READ,
        PERM_DICT_READ,
        PERM_DICT_WRITE,
        PERM_USER_WRITE,
        PERM_REPORT_READ,
    }
)

_READ = frozenset(
    {
        PERM_CATALOG_READ,
        PERM_INBOUND_READ,
        PERM_OUTBOUND_READ,
        PERM_STOCKTAKE_READ,
        PERM_INVENTORY_READ,
        PERM_DICT_READ,
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_ADMIN: _ALL,
    ROLE_SUPERVISOR: frozenset(
        _READ
        | {
            PERM_INBOUND_WRITE,
            PERM_INBOUND_APPROVE,
            PERM_OUTBOUND_WRITE,
            PERM_OUTBOUND_APPROVE,
            PERM_STOCKTAKE_WRITE,
            PERM_STOCKTAKE_APPROVE,
            PERM_AUDIT_READ,
            PERM_REPORT_READ,
        }
    ),
    ROLE_OPERATOR: frozenset(
        _READ
        | {
            PERM_INBOUND_WRITE,
            PERM_OUTBOUND_WRITE,
        }
    ),
    ROLE_VIEWER: frozenset(_READ | {PERM_REPORT_READ}),
}


def has_permission(role_code: str, *required: str) -> bool:
    granted = ROLE_PERMISSIONS.get(role_code, frozenset())
    return all(perm in granted for perm in required)
