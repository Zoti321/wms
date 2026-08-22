"""M3：出库单、出库单行与拣货记录。

Revision ID: 20260821_0004
Revises: 20260821_0003
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0004"
down_revision: Union[str, Sequence[str], None] = "20260821_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbound_order",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
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
        "outbound_order_line",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("planned_qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column(
            "allocated_qty",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "picked_qty",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column("location_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["outbound_order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "pick_record",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("line_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["outbound_order.id"]),
        sa.ForeignKeyConstraint(["line_id"], ["outbound_order_line.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pick_record")
    op.drop_table("outbound_order_line")
    op.drop_table("outbound_order")
