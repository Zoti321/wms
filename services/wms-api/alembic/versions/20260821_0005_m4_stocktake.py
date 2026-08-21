"""M4：盘点单、盘点行与库位作业锁（盘点锁）。

Revision ID: 20260821_0005
Revises: 20260821_0004
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0005"
down_revision: Union[str, Sequence[str], None] = "20260821_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "location_job_lock",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("ref_type", sa.String(length=32), nullable=False),
        sa.Column("ref_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", name="uq_location_job_lock_location"),
    )
    op.create_table(
        "stocktake_order",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("zone", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="counting"),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_table(
        "stocktake_line",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("book_qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("counted_qty", sa.Numeric(precision=18, scale=3), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["stocktake_order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("stocktake_line")
    op.drop_table("stocktake_order")
    op.drop_table("location_job_lock")
