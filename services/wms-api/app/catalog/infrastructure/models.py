"""主数据 ORM 模型。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.catalog.domain.status import ActiveStatus, LocationSpaceStatus
from app.shared.db import Base


class Warehouse(Base):
    __tablename__ = "warehouse"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=ActiveStatus.ACTIVE
    )


class Sku(Base):
    __tablename__ = "sku"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(128), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    safety_stock: Mapped[Decimal] = mapped_column(
        Numeric(18, 3), nullable=False, default=Decimal("0")
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=ActiveStatus.ACTIVE
    )


class Location(Base):
    __tablename__ = "location"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "location_code", name="uq_location_wh_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouse.id"), nullable=False
    )
    location_code: Mapped[str] = mapped_column(String(64), nullable=False)
    zone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    aisle: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    space_status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=LocationSpaceStatus.IDLE
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=ActiveStatus.ACTIVE
    )


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=ActiveStatus.ACTIVE
    )


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=ActiveStatus.ACTIVE
    )
