"""平台：操作日志、字典、用户角色。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.api.schemas import AssignRoleRequest
from app.platform.application import audit_service as audit
from app.platform.application import dict_service, user_service
from app.platform.domain.permissions import (
    PERM_AUDIT_READ,
    PERM_DICT_READ,
    PERM_USER_WRITE,
)
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(tags=["platform"])


@router.get("/operation-logs")
def list_operation_logs(
    operator_id: int | None = None,
    action: str | None = None,
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_AUDIT_READ)),
) -> dict:
    items = audit.list_operation_logs(
        session,
        operator_id=operator_id,
        action=action,
        created_from=created_from,
        created_to=created_to,
    )
    return ok({"items": items})


@router.get("/dictionaries")
def list_dictionaries(
    dict_type: str | None = None,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_DICT_READ)),
) -> dict:
    items = dict_service.list_dict_items(session, dict_type=dict_type)
    return ok({"items": items})


@router.get("/users")
def list_users(
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    return ok({"items": user_service.list_users(session)})


@router.patch("/users/{user_id}/role")
def assign_user_role(
    user_id: int,
    body: AssignRoleRequest,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    try:
        return ok(
            user_service.assign_role(
                session, user_id=user_id, role_code=body.role_code
            )
        )
    except user_service.UserNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body_fail) from exc
    except user_service.RoleNotFoundError as exc:
        body_fail, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail) from exc
