"""出库 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.outbound.api.schemas import (
    ApproveRequest,
    OutboundOrderCreate,
    OutboundOrderUpdate,
    PickRequest,
)
from app.outbound.application import outbound_service as svc
from app.platform.api.deps import CurrentUser, get_current_user
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(prefix="/outbound-orders", tags=["outbound"])


def _raise_outbound(exc: Exception) -> None:
    if isinstance(exc, svc.OutboundNotFoundError):
        body, _ = fail(code=40400, message=str(exc) or "资源不存在", http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body) from exc
    if isinstance(exc, svc.OutboundConflictError):
        body, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body) from exc
    if isinstance(exc, svc.OutboundError):
        body, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body) from exc
    raise exc


def _require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        body_fail, _ = fail(code=40000, message="缺少 Idempotency-Key", http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail)
    return idempotency_key


@router.post("")
def create_outbound_order(
    body: OutboundOrderCreate,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_order(
            session,
            warehouse_id=body.warehouse_id,
            order_type=body.order_type,
            lines=[line.model_dump() for line in body.lines],
            created_by=current_user.id,
            customer_id=body.customer_id,
            remark=body.remark,
            order_no=body.order_no,
        )
    except svc.OutboundError as exc:
        _raise_outbound(exc)
    return JSONResponse(content=ok(data))


@router.get("/{order_id}")
def get_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.get_order(session, order_id))
    except svc.OutboundError as exc:
        _raise_outbound(exc)


@router.patch("/{order_id}")
def update_outbound_order(
    order_id: int,
    body: OutboundOrderUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(
            svc.update_order(
                session,
                order_id,
                lines=(
                    [line.model_dump() for line in body.lines]
                    if body.lines is not None
                    else None
                ),
                customer_id=body.customer_id,
                remark=body.remark,
            )
        )
    except svc.OutboundError as exc:
        _raise_outbound(exc)


@router.post("/{order_id}/submit")
def submit_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.submit_order(session, order_id))
    except svc.OutboundError as exc:
        _raise_outbound(exc)


@router.post("/{order_id}/approve")
def approve_outbound_order(
    order_id: int,
    body: ApproveRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    try:
        return ok(
            svc.approve_order(
                session,
                order_id,
                allocations=[item.model_dump() for item in body.allocations],
                operator_id=current_user.id,
                idempotency_key=key,
            )
        )
    except svc.OutboundError as exc:
        _raise_outbound(exc)


@router.post("/{order_id}/pick")
def pick_outbound_order(
    order_id: int,
    body: PickRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    try:
        return ok(
            svc.pick(
                session,
                order_id,
                line_id=body.line_id,
                location_id=body.location_id,
                qty=body.qty,
                operator_id=current_user.id,
                idempotency_key=key,
            )
        )
    except svc.OutboundError as exc:
        _raise_outbound(exc)


@router.post("/{order_id}/cancel")
def cancel_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
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
    except svc.OutboundError as exc:
        _raise_outbound(exc)
