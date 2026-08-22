"""盘点 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.application import audit_service as audit
from app.platform.domain.permissions import (
    PERM_STOCKTAKE_APPROVE,
    PERM_STOCKTAKE_READ,
    PERM_STOCKTAKE_WRITE,
)
from app.shared.db import get_db
from app.shared.http_errors import DomainErrorRule, map_domain_error, require_idempotency_key
from app.shared.response import ok
from app.stocktake.api.schemas import RecordCountsRequest, StocktakeOrderCreate
from app.stocktake.application import stocktake_service as svc

router = APIRouter(prefix="/stocktakes", tags=["stocktake"])

_STOCKTAKE_RULES = (
    DomainErrorRule(svc.StocktakeNotFoundError, 40400, status.HTTP_404_NOT_FOUND, "资源不存在"),
    DomainErrorRule(svc.StocktakeForbiddenError, 40300, status.HTTP_403_FORBIDDEN),
    DomainErrorRule(svc.StocktakeConflictError, 40900, status.HTTP_409_CONFLICT),
    DomainErrorRule(svc.StocktakeError, 40000, status.HTTP_400_BAD_REQUEST),
)


@router.post("")
def create_stocktake(
    body: StocktakeOrderCreate,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_WRITE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> JSONResponse:
    try:
        data = svc.create_order(
            session,
            warehouse_id=body.warehouse_id,
            zone=body.zone,
            remark=body.remark,
            order_no=body.order_no,
            created_by=current_user.id,
            idempotency_key=idempotency_key,
        )
    except svc.StocktakeError as exc:
        map_domain_error(exc, _STOCKTAKE_RULES)
    return JSONResponse(content=ok(data))


@router.get("/{order_id}")
def get_stocktake(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_READ)),
) -> dict:
    try:
        return ok(svc.get_order(session, order_id))
    except svc.StocktakeError as exc:
        map_domain_error(exc, _STOCKTAKE_RULES)


@router.post("/{order_id}/counts")
def record_stocktake_counts(
    order_id: int,
    body: RecordCountsRequest,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_WRITE)),
) -> dict:
    try:
        return ok(
            svc.record_counts(
                session,
                order_id,
                lines=[line.model_dump() for line in body.lines],
            )
        )
    except svc.StocktakeError as exc:
        map_domain_error(exc, _STOCKTAKE_RULES)


@router.post("/{order_id}/approve")
def approve_stocktake(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_APPROVE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
    try:
        data = svc.approve_order(
            session,
            order_id,
            operator_id=current_user.id,
            role_code=current_user.role_code,
            idempotency_key=idempotency_key,
        )
    except svc.StocktakeError as exc:
        map_domain_error(exc, _STOCKTAKE_RULES)
    if not data.get("replayed"):
        audit.record_operation(
            session,
            operator_id=current_user.id,
            operator_name=current_user.username,
            action=audit.ACTION_STOCKTAKE_APPROVE,
            resource_type="stocktake_order",
            resource_id=order_id,
            commit=True,
        )
    return ok(data)


@router.post("/{order_id}/cancel")
def cancel_stocktake(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_WRITE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
    try:
        return ok(
            svc.cancel_order(
                session,
                order_id,
                operator_id=current_user.id,
                idempotency_key=idempotency_key,
            )
        )
    except svc.StocktakeError as exc:
        map_domain_error(exc, _STOCKTAKE_RULES)
