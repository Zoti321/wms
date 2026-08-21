"""主数据应用用例：CRUD 与停用（不做物理删除）。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog.domain.status import (
    API_TO_SPACE_STATUS,
    SPACE_STATUS_TO_API,
    ActiveStatus,
    LocationSpaceStatus,
)
from app.catalog.infrastructure.models import (
    Customer,
    Location,
    Sku,
    Supplier,
    Warehouse,
)

T = TypeVar("T")


class CatalogConflictError(Exception):
    """业务唯一约束冲突。"""


class CatalogNotFoundError(Exception):
    """主数据不存在。"""


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise CatalogConflictError("编码已存在") from exc


def _get_or_404(session: Session, model: type[T], entity_id: int) -> T:
    entity = session.get(model, entity_id)
    if entity is None:
        raise CatalogNotFoundError
    return entity


def _apply_list_filters(
    stmt: Select[Any],
    *,
    model: type[Any],
    code: str | None,
    name: str | None,
    status: int | None,
    selectable: bool,
    code_attr: str,
) -> Select[Any]:
    if selectable:
        stmt = stmt.where(model.status == ActiveStatus.ACTIVE)
    elif status is not None:
        stmt = stmt.where(model.status == status)
    if code:
        stmt = stmt.where(getattr(model, code_attr).like(f"%{code}%"))
    if name:
        stmt = stmt.where(model.name.like(f"%{name}%"))
    return stmt.order_by(model.id.asc())


def warehouse_to_dict(row: Warehouse) -> dict[str, Any]:
    return {
        "id": row.id,
        "warehouse_code": row.warehouse_code,
        "name": row.name,
        "status": row.status,
    }


def create_warehouse(session: Session, *, warehouse_code: str, name: str) -> dict[str, Any]:
    row = Warehouse(warehouse_code=warehouse_code, name=name, status=ActiveStatus.ACTIVE)
    session.add(row)
    _commit(session)
    session.refresh(row)
    return warehouse_to_dict(row)


def get_warehouse(session: Session, warehouse_id: int) -> dict[str, Any]:
    return warehouse_to_dict(_get_or_404(session, Warehouse, warehouse_id))


def list_warehouses(
    session: Session,
    *,
    code: str | None = None,
    name: str | None = None,
    status: int | None = None,
    selectable: bool = False,
) -> list[dict[str, Any]]:
    stmt = _apply_list_filters(
        select(Warehouse),
        model=Warehouse,
        code=code,
        name=name,
        status=status,
        selectable=selectable,
        code_attr="warehouse_code",
    )
    return [warehouse_to_dict(row) for row in session.scalars(stmt).all()]


def update_warehouse(
    session: Session, warehouse_id: int, *, name: str | None
) -> dict[str, Any]:
    row = _get_or_404(session, Warehouse, warehouse_id)
    if name is not None:
        row.name = name
    _commit(session)
    session.refresh(row)
    return warehouse_to_dict(row)


def deactivate_warehouse(session: Session, warehouse_id: int) -> dict[str, Any]:
    row = _get_or_404(session, Warehouse, warehouse_id)
    active_locations = session.scalars(
        select(Location.id).where(
            Location.warehouse_id == warehouse_id,
            Location.status == ActiveStatus.ACTIVE,
        ).limit(1)
    ).first()
    if active_locations is not None:
        raise CatalogConflictError("仓库仍有启用中的库位，无法停用")
    row.status = ActiveStatus.INACTIVE
    _commit(session)
    session.refresh(row)
    return warehouse_to_dict(row)


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.001'))}"


def sku_to_dict(row: Sku) -> dict[str, Any]:
    return {
        "id": row.id,
        "sku_code": row.sku_code,
        "name": row.name,
        "unit": row.unit,
        "spec": row.spec,
        "barcode": row.barcode,
        "safety_stock": _format_decimal(row.safety_stock),
        "status": row.status,
    }


def create_sku(
    session: Session,
    *,
    sku_code: str,
    name: str,
    unit: str,
    spec: str | None,
    barcode: str | None,
    safety_stock: Decimal,
) -> dict[str, Any]:
    row = Sku(
        sku_code=sku_code,
        name=name,
        unit=unit,
        spec=spec,
        barcode=barcode,
        safety_stock=safety_stock,
        status=ActiveStatus.ACTIVE,
    )
    session.add(row)
    _commit(session)
    session.refresh(row)
    return sku_to_dict(row)


def get_sku(session: Session, sku_id: int) -> dict[str, Any]:
    return sku_to_dict(_get_or_404(session, Sku, sku_id))


def list_skus(
    session: Session,
    *,
    code: str | None = None,
    name: str | None = None,
    status: int | None = None,
    selectable: bool = False,
) -> list[dict[str, Any]]:
    stmt = _apply_list_filters(
        select(Sku),
        model=Sku,
        code=code,
        name=name,
        status=status,
        selectable=selectable,
        code_attr="sku_code",
    )
    return [sku_to_dict(row) for row in session.scalars(stmt).all()]


def update_sku(
    session: Session,
    sku_id: int,
    *,
    name: str | None,
    unit: str | None,
    spec: str | None,
    barcode: str | None,
    safety_stock: Decimal | None,
) -> dict[str, Any]:
    row = _get_or_404(session, Sku, sku_id)
    if name is not None:
        row.name = name
    if unit is not None:
        row.unit = unit
    if spec is not None:
        row.spec = spec
    if barcode is not None:
        row.barcode = barcode
    if safety_stock is not None:
        row.safety_stock = safety_stock
    _commit(session)
    session.refresh(row)
    return sku_to_dict(row)


def deactivate_sku(session: Session, sku_id: int) -> dict[str, Any]:
    row = _get_or_404(session, Sku, sku_id)
    row.status = ActiveStatus.INACTIVE
    _commit(session)
    session.refresh(row)
    return sku_to_dict(row)


def location_to_dict(row: Location) -> dict[str, Any]:
    space = LocationSpaceStatus(row.space_status)
    return {
        "id": row.id,
        "warehouse_id": row.warehouse_id,
        "location_code": row.location_code,
        "zone": row.zone,
        "aisle": row.aisle,
        "bin": row.bin,
        "space_status": SPACE_STATUS_TO_API[space],
        "status": row.status,
    }


def create_location(
    session: Session,
    *,
    warehouse_id: int,
    location_code: str,
    zone: str | None,
    aisle: str | None,
    bin: str | None,
    space_status: str,
) -> dict[str, Any]:
    if session.get(Warehouse, warehouse_id) is None:
        raise CatalogNotFoundError("仓库不存在")
    row = Location(
        warehouse_id=warehouse_id,
        location_code=location_code,
        zone=zone,
        aisle=aisle,
        bin=bin,
        space_status=API_TO_SPACE_STATUS[space_status],
        status=ActiveStatus.ACTIVE,
    )
    session.add(row)
    _commit(session)
    session.refresh(row)
    return location_to_dict(row)


def get_location(session: Session, location_id: int) -> dict[str, Any]:
    return location_to_dict(_get_or_404(session, Location, location_id))


def list_locations(
    session: Session,
    *,
    warehouse_id: int | None = None,
    code: str | None = None,
    status: int | None = None,
    space_status: str | None = None,
    selectable: bool = False,
) -> list[dict[str, Any]]:
    stmt = select(Location)
    if warehouse_id is not None:
        stmt = stmt.where(Location.warehouse_id == warehouse_id)
    if selectable:
        stmt = stmt.where(Location.status == ActiveStatus.ACTIVE)
    elif status is not None:
        stmt = stmt.where(Location.status == status)
    if code:
        stmt = stmt.where(Location.location_code.like(f"%{code}%"))
    if space_status:
        if space_status not in API_TO_SPACE_STATUS:
            raise CatalogConflictError("无效的库位空间状态")
        stmt = stmt.where(
            Location.space_status == API_TO_SPACE_STATUS[space_status]
        )
    stmt = stmt.order_by(Location.id.asc())
    return [location_to_dict(row) for row in session.scalars(stmt).all()]


def update_location(
    session: Session,
    location_id: int,
    *,
    zone: str | None,
    aisle: str | None,
    bin: str | None,
    space_status: str | None,
) -> dict[str, Any]:
    row = _get_or_404(session, Location, location_id)
    if zone is not None:
        row.zone = zone
    if aisle is not None:
        row.aisle = aisle
    if bin is not None:
        row.bin = bin
    if space_status is not None:
        row.space_status = API_TO_SPACE_STATUS[space_status]
    _commit(session)
    session.refresh(row)
    return location_to_dict(row)


def deactivate_location(session: Session, location_id: int) -> dict[str, Any]:
    row = _get_or_404(session, Location, location_id)
    row.status = ActiveStatus.INACTIVE
    _commit(session)
    session.refresh(row)
    return location_to_dict(row)


def supplier_to_dict(row: Supplier) -> dict[str, Any]:
    return {
        "id": row.id,
        "supplier_code": row.supplier_code,
        "name": row.name,
        "status": row.status,
    }


def create_supplier(session: Session, *, supplier_code: str, name: str) -> dict[str, Any]:
    row = Supplier(supplier_code=supplier_code, name=name, status=ActiveStatus.ACTIVE)
    session.add(row)
    _commit(session)
    session.refresh(row)
    return supplier_to_dict(row)


def get_supplier(session: Session, supplier_id: int) -> dict[str, Any]:
    return supplier_to_dict(_get_or_404(session, Supplier, supplier_id))


def list_suppliers(
    session: Session,
    *,
    code: str | None = None,
    name: str | None = None,
    status: int | None = None,
    selectable: bool = False,
) -> list[dict[str, Any]]:
    stmt = _apply_list_filters(
        select(Supplier),
        model=Supplier,
        code=code,
        name=name,
        status=status,
        selectable=selectable,
        code_attr="supplier_code",
    )
    return [supplier_to_dict(row) for row in session.scalars(stmt).all()]


def update_supplier(
    session: Session, supplier_id: int, *, name: str | None
) -> dict[str, Any]:
    row = _get_or_404(session, Supplier, supplier_id)
    if name is not None:
        row.name = name
    _commit(session)
    session.refresh(row)
    return supplier_to_dict(row)


def deactivate_supplier(session: Session, supplier_id: int) -> dict[str, Any]:
    row = _get_or_404(session, Supplier, supplier_id)
    row.status = ActiveStatus.INACTIVE
    _commit(session)
    session.refresh(row)
    return supplier_to_dict(row)


def customer_to_dict(row: Customer) -> dict[str, Any]:
    return {
        "id": row.id,
        "customer_code": row.customer_code,
        "name": row.name,
        "status": row.status,
    }


def create_customer(session: Session, *, customer_code: str, name: str) -> dict[str, Any]:
    row = Customer(customer_code=customer_code, name=name, status=ActiveStatus.ACTIVE)
    session.add(row)
    _commit(session)
    session.refresh(row)
    return customer_to_dict(row)


def get_customer(session: Session, customer_id: int) -> dict[str, Any]:
    return customer_to_dict(_get_or_404(session, Customer, customer_id))


def list_customers(
    session: Session,
    *,
    code: str | None = None,
    name: str | None = None,
    status: int | None = None,
    selectable: bool = False,
) -> list[dict[str, Any]]:
    stmt = _apply_list_filters(
        select(Customer),
        model=Customer,
        code=code,
        name=name,
        status=status,
        selectable=selectable,
        code_attr="customer_code",
    )
    return [customer_to_dict(row) for row in session.scalars(stmt).all()]


def update_customer(
    session: Session, customer_id: int, *, name: str | None
) -> dict[str, Any]:
    row = _get_or_404(session, Customer, customer_id)
    if name is not None:
        row.name = name
    _commit(session)
    session.refresh(row)
    return customer_to_dict(row)


def deactivate_customer(session: Session, customer_id: int) -> dict[str, Any]:
    row = _get_or_404(session, Customer, customer_id)
    row.status = ActiveStatus.INACTIVE
    _commit(session)
    session.refresh(row)
    return customer_to_dict(row)
