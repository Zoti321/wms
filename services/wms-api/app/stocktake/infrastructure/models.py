"""盘点单与盘点行 ORM。"""

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


class StocktakeOrder(Base):
    __tablename__ = "stocktake_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    zone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="counting")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.utc_timestamp(),
        nullable=False,
    )

    lines: Mapped[list[StocktakeLine]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class StocktakeLine(Base):
    __tablename__ = "stocktake_line"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("stocktake_order.id"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    book_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), nullable=False)
    counted_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)

    order: Mapped[StocktakeOrder] = relationship(back_populates="lines")
