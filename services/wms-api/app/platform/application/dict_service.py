"""基础字典查询。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.platform.infrastructure.models import DictItem


def list_dict_items(
    session: Session,
    *,
    dict_type: str | None = None,
) -> list[dict]:
    stmt = select(DictItem).where(DictItem.status == 1)
    if dict_type is not None:
        stmt = stmt.where(DictItem.dict_type == dict_type)
    stmt = stmt.order_by(DictItem.dict_type.asc(), DictItem.sort_order.asc(), DictItem.id.asc())
    rows = session.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "dict_type": row.dict_type,
            "code": row.code,
            "name": row.name,
            "sort_order": row.sort_order,
        }
        for row in rows
    ]
