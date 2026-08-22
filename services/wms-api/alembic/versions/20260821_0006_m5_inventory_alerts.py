"""M5：库存预警表（仓+SKU 汇总可用 vs 安全库存）。

Revision ID: 20260821_0006
Revises: 20260821_0005
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0006"
down_revision: Union[str, Sequence[str], None] = "20260821_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_alert",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("qty_available", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("safety_stock", sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.Column("cleared_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_id", "sku_id", name="uq_inventory_alert_wh_sku"),
    )


def downgrade() -> None:
    op.drop_table("inventory_alert")
