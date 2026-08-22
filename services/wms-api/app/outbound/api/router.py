"""出库 HTTP 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.outbound.api.schemas import (
    ApproveRequest,
    OutboundOrderCreate,
    OutboundOrderUpdate,
    PickRequest,
)
from app.outbound.application import outbound_service as svc
from app.platform.api.deps import CurrentUser, require_permissions
from app.platform.application import audit_service as audit
from app.platform.domain.permissions import (
    PERM_OUTBOUND_APPROVE,
    PERM_OUTBOUND_READ,
    PERM_OUTBOUND_WRITE,
)
from app.shared.db import get_db
from app.shared.http_errors import DomainErrorRule, map_domain_error, require_idempotency_key
from app.shared.response import ok

router = APIRouter(prefix="/outbound-orders", tags=["outbound"])

_OUTBOUND_RULES = (
    DomainErrorRule(svc.OutboundNotFoundError, 40400, status.HTTP_404_NOT_FOUND, "资源不存在"),
    DomainErrorRule(svc.OutboundConflictError, 40900, status.HTTP_409_CONFLICT),
    DomainErrorRule(svc.OutboundError, 40000, status.HTTP_400_BAD_REQUEST),
)


@router.post("")
def create_outbound_order(
    body: OutboundOrderCreate,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_WRITE)),
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
        map_domain_error(exc, _OUTBOUND_RULES)
    return JSONResponse(content=ok(data))


@router.get("/{order_id}")
def get_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_READ)),
) -> dict:
    try:
        return ok(svc.get_order(session, order_id))
    except svc.OutboundError as exc:
        map_domain_error(exc, _OUTBOUND_RULES)


@router.patch("/{order_id}")
def update_outbound_order(
    order_id: int,
    body: OutboundOrderUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_WRITE)),
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
        map_domain_error(exc, _OUTBOUND_RULES)


@router.post("/{order_id}/submit")
def submit_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_WRITE)),
) -> dict:
    try:
        return ok(svc.submit_order(session, order_id))
    except svc.OutboundError as exc:
        map_domain_error(exc, _OUTBOUND_RULES)


@router.post("/{order_id}/approve")
def approve_outbound_order(
    order_id: int,
    body: ApproveRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_APPROVE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
    try:
        data = svc.approve_order(
            session,
            order_id,
            allocations=[item.model_dump() for item in body.allocations],
            operator_id=current_user.id,
            idempotency_key=idempotency_key,
        )
    except svc.OutboundError as exc:
        map_domain_error(exc, _OUTBOUND_RULES)
    if not data.get("replayed"):
        audit.record_operation(
            session,
            operator_id=current_user.id,
            operator_name=current_user.username,
            action=audit.ACTION_OUTBOUND_APPROVE,
            resource_type="outbound_order",
            resource_id=order_id,
            commit=True,
        )
    return ok(data)


@router.post("/{order_id}/pick")
def pick_outbound_order(
    order_id: int,
    body: PickRequest,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_WRITE)),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
    try:
        return ok(
            svc.pick(
                session,
                order_id,
                line_id=body.line_id,
                location_id=body.location_id,
                qty=body.qty,
                operator_id=current_user.id,
                idempotency_key=idempotency_key,
            )
        )
    except svc.OutboundError as exc:
        map_domain_error(exc, _OUTBOUND_RULES)


@router.post("/{order_id}/cancel")
def cancel_outbound_order(
    order_id: int,
    session: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions(PERM_OUTBOUND_WRITE)),
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
    except svc.OutboundError as exc:
        map_domain_error(exc, _OUTBOUND_RULES)
