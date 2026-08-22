"""盘点 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
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
from app.shared.response import fail, ok
from app.stocktake.api.schemas import RecordCountsRequest, StocktakeOrderCreate
from app.stocktake.application import stocktake_service as svc

router = APIRouter(prefix="/stocktakes", tags=["stocktake"])


def _raise_stocktake(exc: Exception) -> None:
    if isinstance(exc, svc.StocktakeNotFoundError):
        body, _ = fail(code=40400, message=str(exc) or "资源不存在", http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body) from exc
    if isinstance(exc, svc.StocktakeForbiddenError):
        body, _ = fail(code=40300, message=str(exc), http_status=403)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=body) from exc
    if isinstance(exc, svc.StocktakeConflictError):
        body, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body) from exc
    if isinstance(exc, svc.StocktakeError):
        body, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body) from exc
    raise exc


def _require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        body_fail, _ = fail(code=40000, message="缺少 Idempotency-Key", http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail)
    return idempotency_key


@router.post("")
def create_stocktake(
    body: StocktakeOrderCreate,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_WRITE)),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JSONResponse:
    key = _require_idempotency_key(idempotency_key)
    try:
        data = svc.create_order(
            session,
            warehouse_id=body.warehouse_id,
            zone=body.zone,
            remark=body.remark,
            order_no=body.order_no,
            created_by=current_user.id,
            idempotency_key=key,
        )
    except svc.StocktakeError as exc:
        _raise_stocktake(exc)
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
        _raise_stocktake(exc)


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
        _raise_stocktake(exc)


@router.post("/{order_id}/approve")
def approve_stocktake(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_STOCKTAKE_APPROVE)),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    try:
        data = svc.approve_order(
            session,
            order_id,
            operator_id=current_user.id,
            role_code=current_user.role_code,
            idempotency_key=key,
        )
    except svc.StocktakeError as exc:
        _raise_stocktake(exc)
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
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    try:
        return ok(
            svc.cancel_order(
                session,
                order_id,
                operator_id=current_user.id,
                idempotency_key=key,
            )
        )
    except svc.StocktakeError as exc:
        _raise_stocktake(exc)
