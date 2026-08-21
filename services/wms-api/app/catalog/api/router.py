"""主数据 HTTP 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.catalog.api.schemas import (
    CustomerCreate,
    CustomerData,
    CustomerUpdate,
    LocationCreate,
    LocationData,
    LocationUpdate,
    SkuCreate,
    SkuData,
    SkuUpdate,
    SupplierCreate,
    SupplierData,
    SupplierUpdate,
    WarehouseCreate,
    WarehouseData,
    WarehouseUpdate,
)
from app.catalog.application import catalog_service as svc
from app.platform.api.deps import CurrentUser, get_current_user
from app.shared.db import get_db
from app.shared.response import fail, ok

router = APIRouter(tags=["catalog"])


def _raise_catalog_error(exc: Exception) -> None:
    if isinstance(exc, svc.CatalogNotFoundError):
        message = str(exc) if str(exc) else "资源不存在"
        body, _ = fail(code=40400, message=message, http_status=404)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=body) from exc
    if isinstance(exc, svc.CatalogConflictError):
        body, _ = fail(code=40900, message=str(exc) or "编码已存在", http_status=409)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=body) from exc
    raise exc


def _ok_item(model: type, data: dict[str, Any]) -> dict[str, Any]:
    return ok(model.model_validate(data).model_dump())


def _ok_items(model: type, items: list[dict[str, Any]]) -> dict[str, Any]:
    return ok({"items": [model.model_validate(item).model_dump() for item in items]})


# --- warehouses ---


@router.post("/warehouses")
def create_warehouse(
    body: WarehouseCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_warehouse(
            session, warehouse_code=body.warehouse_code, name=body.name
        )
    except svc.CatalogConflictError as exc:
        _raise_catalog_error(exc)
    return JSONResponse(content=_ok_item(WarehouseData, data))


@router.get("/warehouses")
def list_warehouses(
    code: str | None = None,
    name: str | None = None,
    entity_status: int | None = Query(default=None, alias="status", ge=0, le=1),
    selectable: bool = False,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    items = svc.list_warehouses(
        session,
        code=code,
        name=name,
        status=entity_status,
        selectable=selectable,
    )
    return _ok_items(WarehouseData, items)


@router.get("/warehouses/{warehouse_id}")
def get_warehouse(
    warehouse_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(WarehouseData, svc.get_warehouse(session, warehouse_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


@router.patch("/warehouses/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            WarehouseData,
            svc.update_warehouse(session, warehouse_id, name=body.name),
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


@router.post("/warehouses/{warehouse_id}/deactivate")
def deactivate_warehouse(
    warehouse_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            WarehouseData, svc.deactivate_warehouse(session, warehouse_id)
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


# --- skus ---


@router.post("/skus")
def create_sku(
    body: SkuCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_sku(
            session,
            sku_code=body.sku_code,
            name=body.name,
            unit=body.unit,
            spec=body.spec,
            barcode=body.barcode,
            safety_stock=body.safety_stock,
        )
    except svc.CatalogConflictError as exc:
        _raise_catalog_error(exc)
    return JSONResponse(content=_ok_item(SkuData, data))


@router.get("/skus")
def list_skus(
    code: str | None = None,
    name: str | None = None,
    entity_status: int | None = Query(default=None, alias="status", ge=0, le=1),
    selectable: bool = False,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    # SKU 跨仓共享；「按仓筛可用 SKU」= 受保护列表 + selectable（启用中）
    items = svc.list_skus(
        session,
        code=code,
        name=name,
        status=entity_status,
        selectable=selectable,
    )
    return _ok_items(SkuData, items)


@router.get("/skus/{sku_id}")
def get_sku(
    sku_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(SkuData, svc.get_sku(session, sku_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


@router.patch("/skus/{sku_id}")
def update_sku(
    sku_id: int,
    body: SkuUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            SkuData,
            svc.update_sku(
                session,
                sku_id,
                name=body.name,
                unit=body.unit,
                spec=body.spec,
                barcode=body.barcode,
                safety_stock=body.safety_stock,
            ),
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


@router.post("/skus/{sku_id}/deactivate")
def deactivate_sku(
    sku_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(SkuData, svc.deactivate_sku(session, sku_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


# --- locations ---


@router.post("/locations")
def create_location(
    body: LocationCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_location(
            session,
            warehouse_id=body.warehouse_id,
            location_code=body.location_code,
            zone=body.zone,
            aisle=body.aisle,
            bin=body.bin,
            space_status=body.space_status,
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)
    return JSONResponse(content=_ok_item(LocationData, data))


@router.get("/locations")
def list_locations(
    warehouse_id: int | None = None,
    code: str | None = None,
    entity_status: int | None = Query(default=None, alias="status", ge=0, le=1),
    space_status: str | None = None,
    selectable: bool = False,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        items = svc.list_locations(
            session,
            warehouse_id=warehouse_id,
            code=code,
            status=entity_status,
            space_status=space_status,
            selectable=selectable,
        )
    except svc.CatalogConflictError as exc:
        _raise_catalog_error(exc)
    return _ok_items(LocationData, items)


@router.get("/locations/{location_id}")
def get_location(
    location_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(LocationData, svc.get_location(session, location_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


@router.patch("/locations/{location_id}")
def update_location(
    location_id: int,
    body: LocationUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            LocationData,
            svc.update_location(
                session,
                location_id,
                zone=body.zone,
                aisle=body.aisle,
                bin=body.bin,
                space_status=body.space_status,
            ),
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


@router.post("/locations/{location_id}/deactivate")
def deactivate_location(
    location_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(LocationData, svc.deactivate_location(session, location_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


# --- suppliers ---


@router.post("/suppliers")
def create_supplier(
    body: SupplierCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_supplier(
            session, supplier_code=body.supplier_code, name=body.name
        )
    except svc.CatalogConflictError as exc:
        _raise_catalog_error(exc)
    return JSONResponse(content=_ok_item(SupplierData, data))


@router.get("/suppliers")
def list_suppliers(
    code: str | None = None,
    name: str | None = None,
    entity_status: int | None = Query(default=None, alias="status", ge=0, le=1),
    selectable: bool = False,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    items = svc.list_suppliers(
        session,
        code=code,
        name=name,
        status=entity_status,
        selectable=selectable,
    )
    return _ok_items(SupplierData, items)


@router.get("/suppliers/{supplier_id}")
def get_supplier(
    supplier_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(SupplierData, svc.get_supplier(session, supplier_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


@router.patch("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            SupplierData,
            svc.update_supplier(session, supplier_id, name=body.name),
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


@router.post("/suppliers/{supplier_id}/deactivate")
def deactivate_supplier(
    supplier_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(SupplierData, svc.deactivate_supplier(session, supplier_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


# --- customers ---


@router.post("/customers")
def create_customer(
    body: CustomerCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    try:
        data = svc.create_customer(
            session, customer_code=body.customer_code, name=body.name
        )
    except svc.CatalogConflictError as exc:
        _raise_catalog_error(exc)
    return JSONResponse(content=_ok_item(CustomerData, data))


@router.get("/customers")
def list_customers(
    code: str | None = None,
    name: str | None = None,
    entity_status: int | None = Query(default=None, alias="status", ge=0, le=1),
    selectable: bool = False,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    items = svc.list_customers(
        session,
        code=code,
        name=name,
        status=entity_status,
        selectable=selectable,
    )
    return _ok_items(CustomerData, items)


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(CustomerData, svc.get_customer(session, customer_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)


@router.patch("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(
            CustomerData,
            svc.update_customer(session, customer_id, name=body.name),
        )
    except (svc.CatalogConflictError, svc.CatalogNotFoundError) as exc:
        _raise_catalog_error(exc)


@router.post("/customers/{customer_id}/deactivate")
def deactivate_customer(
    customer_id: int,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        return _ok_item(CustomerData, svc.deactivate_customer(session, customer_id))
    except svc.CatalogNotFoundError as exc:
        _raise_catalog_error(exc)
