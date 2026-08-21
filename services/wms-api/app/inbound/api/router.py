"""入库 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.inbound.api.schemas import InboundOrderCreate, InboundOrderUpdate, PutawayRequest
from app.inbound.application import inbound_service as svc
from app.platform.api.deps import CurrentUser, get_current_user
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(prefix="/inbound-orders", tags=["inbound"])


def _raise_inbound(exc: Exception) -> None:
    if isinstance(exc, svc.InboundNotFoundError):
        body, _ = fail(code=40400, message=str(exc) or "资源不存在", http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body) from exc
    if isinstance(exc, svc.InboundConflictError):
        body, _ = fail(code=40900, message=str(exc), http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body) from exc
    if isinstance(exc, svc.InboundError):
        body, _ = fail(code=40000, message=str(exc), http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body) from exc
    raise exc


@router.post("")
def create_inbound_order(
    body: InboundOrderCreate,
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
            supplier_id=body.supplier_id,
            remark=body.remark,
            order_no=body.order_no,
        )
    except svc.InboundError as exc:
        _raise_inbound(exc)
    return JSONResponse(content=ok(data))


@router.get("/{order_id}")
def get_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.get_order(session, order_id))
    except svc.InboundError as exc:
        _raise_inbound(exc)


@router.patch("/{order_id}")
def update_inbound_order(
    order_id: int,
    body: InboundOrderUpdate,
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
                supplier_id=body.supplier_id,
                remark=body.remark,
            )
        )
    except svc.InboundError as exc:
        _raise_inbound(exc)


@router.post("/{order_id}/submit")
def submit_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.submit_order(session, order_id))
    except svc.InboundError as exc:
        _raise_inbound(exc)


@router.post("/{order_id}/approve")
def approve_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.approve_order(session, order_id))
    except svc.InboundError as exc:
        _raise_inbound(exc)


@router.post("/{order_id}/cancel")
def cancel_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return ok(svc.cancel_order(session, order_id))
    except svc.InboundError as exc:
        _raise_inbound(exc)


@router.post("/{order_id}/putaway")
def putaway_inbound_order(
    order_id: int,
    body: PutawayRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    if not idempotency_key:
        body_fail, _ = fail(code=40000, message="缺少 Idempotency-Key", http_status=400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=body_fail)
    try:
        return ok(
            svc.putaway(
                session,
                order_id,
                line_id=body.line_id,
                location_id=body.location_id,
                qty=body.qty,
                operator_id=current_user.id,
                idempotency_key=idempotency_key,
            )
        )
    except svc.InboundError as exc:
        _raise_inbound(exc)
