"""入库单、入库单行与上架记录 ORM。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db import Base


class InboundOrder(Base):
    __tablename__ = "inbound_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    supplier_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.utc_timestamp(),
        nullable=False,
    )

    lines: Mapped[list[InboundOrderLine]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class InboundOrderLine(Base):
    __tablename__ = "inbound_order_line"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("inbound_order.id"), nullable=False
    )
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    putaway_qty: Mapped[Decimal] = mapped_column(
        Numeric(18, 3), nullable=False, default=Decimal("0")
    )

    order: Mapped[InboundOrder] = relationship(back_populates="lines")


class PutawayRecord(Base):
    __tablename__ = "putaway_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("inbound_order.id"), nullable=False
    )
    line_id: Mapped[int] = mapped_column(
        ForeignKey("inbound_order_line.id"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    operator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.utc_timestamp(),
        nullable=False,
    )
