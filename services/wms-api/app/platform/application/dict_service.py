"""基础字典查询与维护。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.platform.infrastructure.models import DictItem
from app.shared.pagination import paginate, paginated_payload


class DictError(Exception):
    """字典业务错误。"""


class DictNotFoundError(DictError):
    """字典项不存在。"""


class DictConflictError(DictError):
    """字典项编码冲突。"""


def _item_to_dict(row: DictItem) -> dict:
    return {
        "id": row.id,
        "dict_type": row.dict_type,
        "code": row.code,
        "name": row.name,
        "sort_order": row.sort_order,
        "status": row.status,
    }


def _get_item(session: Session, item_id: int) -> DictItem:
    item = session.get(DictItem, item_id)
    if item is None:
        raise DictNotFoundError("字典项不存在")
    return item


def list_dict_items(
    session: Session,
    *,
    dict_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    stmt = select(DictItem).where(DictItem.status == 1)
    if dict_type is not None:
        stmt = stmt.where(DictItem.dict_type == dict_type)
    stmt = stmt.order_by(
        DictItem.dict_type.asc(), DictItem.sort_order.asc(), DictItem.id.asc()
    )
    rows, total = paginate(session, stmt, page=page, page_size=page_size)
    return paginated_payload(
        [
            {
                "id": row.id,
                "dict_type": row.dict_type,
                "code": row.code,
                "name": row.name,
                "sort_order": row.sort_order,
            }
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_dict_item(
    session: Session,
    *,
    dict_type: str,
    code: str,
    name: str,
    sort_order: int = 0,
) -> dict:
    item = DictItem(
        dict_type=dict_type,
        code=code,
        name=name,
        sort_order=sort_order,
        status=1,
    )
    session.add(item)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DictConflictError("字典编码已存在") from exc
    session.refresh(item)
    return _item_to_dict(item)


def update_dict_item(
    session: Session,
    item_id: int,
    *,
    name: str | None = None,
    sort_order: int | None = None,
) -> dict:
    item = _get_item(session, item_id)
    if item.status != 1:
        raise DictConflictError("字典项已停用")
    if name is not None:
        item.name = name
    if sort_order is not None:
        item.sort_order = sort_order
    session.commit()
    session.refresh(item)
    return _item_to_dict(item)


def deactivate_dict_item(session: Session, item_id: int) -> dict:
    item = _get_item(session, item_id)
    if item.status != 1:
        raise DictConflictError("字典项已停用")
    item.status = 0
    session.commit()
    session.refresh(item)
    return _item_to_dict(item)
