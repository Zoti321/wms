"""库位作业锁（盘点锁等）——独立于冻结数量与库位主数据冻结状态。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base


class LocationJobLock(Base):
    __tablename__ = "location_job_lock"
    __table_args__ = (
        UniqueConstraint("location_id", name="uq_location_job_lock_location"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ref_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.utc_timestamp(),
        nullable=False,
    )
