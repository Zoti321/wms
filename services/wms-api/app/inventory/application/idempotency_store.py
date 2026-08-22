"""MySQL 幂等存储 adapter（库存上下文内部 seam）。"""

from __future__ import annotations

import json
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.inventory.application.types import MutationResult
from app.inventory.infrastructure.models import IdempotencyRecord


def replay(result: MutationResult) -> MutationResult:
    return MutationResult(
        inventory_id=result.inventory_id,
        qty_on_hand=result.qty_on_hand,
        qty_frozen=result.qty_frozen,
        qty_available=result.qty_available,
        version=result.version,
        ledger_id=result.ledger_id,
        replayed=True,
    )


def load_mutation(
    session: Session, *, scope: str, key: str
) -> MutationResult | None:
    row = session.scalars(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == key,
        )
    ).first()
    if row is None:
        return None
    payload = json.loads(row.response_json)
    return MutationResult(**payload)


def store_mutation(
    session: Session, *, scope: str, key: str, result: MutationResult
) -> None:
    session.add(
        IdempotencyRecord(
            scope=scope,
            idempotency_key=key,
            response_json=json.dumps(asdict(result)),
        )
    )


def try_replay(
    session: Session, *, scope: str, key: str
) -> MutationResult | None:
    existing = load_mutation(session, scope=scope, key=key)
    if existing is None:
        return None
    return replay(existing)


def load_json(
    session: Session, *, scope: str, idempotency_key: str
) -> dict | None:
    """供入/出库适配器复用同一幂等表（不直连基础设施模型）。"""
    row = session.scalars(
        select(IdempotencyRecord).where(
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
    ).first()
    if row is None:
        return None
    return json.loads(row.response_json)


def store_json(
    session: Session, *, scope: str, idempotency_key: str, payload: dict
) -> None:
    session.add(
        IdempotencyRecord(
            scope=scope,
            idempotency_key=idempotency_key,
            response_json=json.dumps(payload),
        )
    )
