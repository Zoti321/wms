"""平台：操作日志、字典、用户角色、基础报表。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.api.schemas import (
    AssignRoleRequest,
    CreateDictItemRequest,
    CreateUserRequest,
    DailyReportData,
    ResetPasswordRequest,
    UpdateDictItemRequest,
)
from app.platform.application import audit_service as audit
from app.platform.application import dict_service, report_service, user_service
from app.platform.domain.permissions import (
    PERM_AUDIT_READ,
    PERM_DICT_READ,
    PERM_DICT_WRITE,
    PERM_REPORT_READ,
    PERM_USER_WRITE,
)
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(tags=["platform"])


def _daily_report_or_raise(
    session: Session, *, warehouse_id: int, business_date: str
) -> dict:
    try:
        day = report_service.parse_business_date(business_date)
        return report_service.get_daily_report(
            session, warehouse_id=warehouse_id, business_date=day
        )
    except report_service.ReportValidationError as exc:
        body_fail, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail
        ) from exc
    except report_service.ReportNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=body_fail
        ) from exc


@router.get("/reports/daily")
def get_daily_report(
    warehouse_id: int = Query(...),
    business_date: str = Query(..., description="UTC 业务日 YYYY-MM-DD"),
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_REPORT_READ)),
) -> dict:
    raw = _daily_report_or_raise(
        session, warehouse_id=warehouse_id, business_date=business_date
    )
    return ok(DailyReportData.model_validate(raw).model_dump())


@router.get("/reports/daily.csv")
def export_daily_report_csv(
    warehouse_id: int = Query(...),
    business_date: str = Query(..., description="UTC 业务日 YYYY-MM-DD"),
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_REPORT_READ)),
) -> Response:
    report = _daily_report_or_raise(
        session, warehouse_id=warehouse_id, business_date=business_date
    )
    content = report_service.daily_report_to_csv(report)
    filename = f"daily-report-{business_date}-wh{warehouse_id}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@router.post("/dictionaries")
def create_dictionary_item(
    body: CreateDictItemRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_DICT_WRITE)),
) -> dict:
    try:
        data = dict_service.create_dict_item(
            session,
            dict_type=body.dict_type,
            code=body.code,
            name=body.name,
            sort_order=body.sort_order,
        )
    except dict_service.DictConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_DICT_CREATE,
        resource_type="dict_item",
        resource_id=data["id"],
        detail=f"{data['dict_type']}:{data['code']}",
        commit=True,
    )
    return ok(data)


@router.patch("/dictionaries/{item_id}")
def update_dictionary_item(
    item_id: int,
    body: UpdateDictItemRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_DICT_WRITE)),
) -> dict:
    try:
        data = dict_service.update_dict_item(
            session,
            item_id,
            name=body.name,
            sort_order=body.sort_order,
        )
    except dict_service.DictNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body_fail) from exc
    except dict_service.DictConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_DICT_UPDATE,
        resource_type="dict_item",
        resource_id=item_id,
        commit=True,
    )
    return ok(data)


@router.post("/dictionaries/{item_id}/deactivate")
def deactivate_dictionary_item(
    item_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_DICT_WRITE)),
) -> dict:
    try:
        data = dict_service.deactivate_dict_item(session, item_id)
    except dict_service.DictNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body_fail) from exc
    except dict_service.DictConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_DICT_DEACTIVATE,
        resource_type="dict_item",
        resource_id=item_id,
        commit=True,
    )
    return ok(data)


@router.get("/users")
def list_users(
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    return ok({"items": user_service.list_users(session)})


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    try:
        data = user_service.create_user(
            session,
            username=body.username,
            password=body.password,
            role_code=body.role_code,
        )
    except user_service.UserConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    except user_service.RoleNotFoundError as exc:
        body_fail, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_USER_CREATE,
        resource_type="user",
        resource_id=data["id"],
        detail=data["username"],
        commit=True,
    )
    return ok(data)


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    try:
        data = user_service.deactivate_user(
            session, user_id=user_id, operator_id=current_user.id
        )
    except user_service.UserNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body_fail) from exc
    except user_service.UserConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_USER_DEACTIVATE,
        resource_type="user",
        resource_id=user_id,
        detail=data["username"],
        commit=True,
    )
    return ok(data)


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_USER_WRITE)),
) -> dict:
    try:
        data = user_service.reset_password(
            session, user_id=user_id, password=body.password
        )
    except user_service.UserNotFoundError as exc:
        body_fail, _ = fail(code=40400, message=str(exc), http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body_fail) from exc
    except user_service.UserConflictError as exc:
        body_fail, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body_fail) from exc
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_USER_RESET_PASSWORD,
        resource_type="user",
        resource_id=user_id,
        detail=data["username"],
        commit=True,
    )
    return ok(data)


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
