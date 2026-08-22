"""分页查询参数与 SQLAlchemy 列表结果。"""

from __future__ import annotations

from typing import Any

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def pagination_query(
    page: int = Query(DEFAULT_PAGE, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"每页条数，默认 {DEFAULT_PAGE_SIZE}，上限 {MAX_PAGE_SIZE}",
    ),
) -> tuple[int, int]:
    return page, page_size


def paginate(
    session: Session,
    stmt: Select[Any],
    *,
    page: int,
    page_size: int,
) -> tuple[list[Any], int]:
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    offset = (page - 1) * page_size
    rows = list(session.scalars(stmt.offset(offset).limit(page_size)).all())
    return rows, total


def paginated_payload(
    items: list[Any],
    *,
    total: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
