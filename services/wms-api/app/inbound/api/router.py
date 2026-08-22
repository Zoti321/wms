"""入库 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.inbound.api.schemas import InboundOrderCreate, InboundOrderUpdate, PutawayRequest
from app.inbound.application import inbound_service as svc
from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.application import audit_service as audit
from app.platform.domain.permissions import (
    PERM_INBOUND_APPROVE,
    PERM_INBOUND_READ,
    PERM_INBOUND_WRITE,
)
from app.shared.db import get_db
from app.shared.http_errors import DomainErrorRule, map_domain_error, require_idempotency_key
from app.shared.response import ok

router = APIRouter(prefix="/inbound-orders", tags=["inbound"])

_INBOUND_RULES = (
    DomainErrorRule(svc.InboundNotFoundError, 40400, status.HTTP_404_NOT_FOUND, "资源不存在"),
    DomainErrorRule(svc.InboundConflictError, 40900, status.HTTP_409_CONFLICT),
    DomainErrorRule(svc.InboundError, 40000, status.HTTP_400_BAD_REQUEST),
)


@router.post("")
def create_inbound_order(
    body: InboundOrderCreate,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_INBOUND_WRITE)),
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
        map_domain_error(exc, _INBOUND_RULES)
    return JSONResponse(content=ok(data))


@router.get("/{order_id}")
def get_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INBOUND_READ)),
) -> dict:
    try:
        return ok(svc.get_order(session, order_id))
    except svc.InboundError as exc:
        map_domain_error(exc, _INBOUND_RULES)


@router.patch("/{order_id}")
def update_inbound_order(
    order_id: int,
    body: InboundOrderUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INBOUND_WRITE)),
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
        map_domain_error(exc, _INBOUND_RULES)


@router.post("/{order_id}/submit")
def submit_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INBOUND_WRITE)),
) -> dict:
    try:
        return ok(svc.submit_order(session, order_id))
    except svc.InboundError as exc:
        map_domain_error(exc, _INBOUND_RULES)


@router.post("/{order_id}/approve")
def approve_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_INBOUND_APPROVE)),
) -> dict:
    try:
        data = svc.approve_order(session, order_id)
    except svc.InboundError as exc:
        map_domain_error(exc, _INBOUND_RULES)
    audit.record_operation(
        session,
        operator_id=current_user.id,
        operator_name=current_user.username,
        action=audit.ACTION_INBOUND_APPROVE,
        resource_type="inbound_order",
        resource_id=order_id,
        commit=True,
    )
    return ok(data)


@router.post("/{order_id}/cancel")
def cancel_inbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_INBOUND_WRITE)),
) -> dict:
    try:
        return ok(svc.cancel_order(session, order_id))
    except svc.InboundError as exc:
        map_domain_error(exc, _INBOUND_RULES)


@router.post("/{order_id}/putaway")
def putaway_inbound_order(
    order_id: int,
    body: PutawayRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_INBOUND_WRITE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
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
        map_domain_error(exc, _INBOUND_RULES)
