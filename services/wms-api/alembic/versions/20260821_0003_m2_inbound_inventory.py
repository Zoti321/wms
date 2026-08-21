"""M2：库存余额/流水、幂等键、入库单与上架记录。

Revision ID: 20260821_0003
Revises: 20260821_0002
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0003"
down_revision: Union[str, Sequence[str], None] = "20260821_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "qty_on_hand",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "qty_frozen",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "warehouse_id", "sku_id", "location_id", name="uq_inventory_wh_sku_loc"
        ),
    )
    op.create_table(
        "inventory_ledger",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("change_qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("bal_qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("ref_type", sa.String(length=32), nullable=False),
        sa.Column("ref_id", sa.BigInteger(), nullable=False),
        sa.Column("ref_line_id", sa.BigInteger(), nullable=True),
        sa.Column("ref_no", sa.String(length=64), nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "idempotency_record",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scope", "idempotency_key", name="uq_idempotency_scope_key"
        ),
    )
    op.create_table(
        "inbound_order",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("supplier_id", sa.BigInteger(), nullable=True),
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
        "inbound_order_line",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("planned_qty", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column(
            "putaway_qty",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["inbound_order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "putaway_record",
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
        sa.ForeignKeyConstraint(["order_id"], ["inbound_order.id"]),
        sa.ForeignKeyConstraint(["line_id"], ["inbound_order_line.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("putaway_record")
    op.drop_table("inbound_order_line")
    op.drop_table("inbound_order")
    op.drop_table("idempotency_record")
    op.drop_table("inventory_ledger")
    op.drop_table("inventory")
