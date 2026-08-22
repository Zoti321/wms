"""M1：主数据表（SKU / 库位 / 供应商 / 客户）。

Revision ID: 20260821_0002
Revises: 20260821_0001
Create Date: 2026-08-21

仓库表已在 M0 创建；本迁移扩展库位层级字段语义（区/排/位）及往来单位。
库位 space_status 表示空间资源状态，勿与库存冻结数量混淆。
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0002"
down_revision: Union[str, Sequence[str], None] = "20260821_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sku",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sku_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("spec", sa.String(length=128), nullable=True),
        sa.Column("barcode", sa.String(length=64), nullable=True),
        sa.Column(
            "safety_stock",
            sa.Numeric(precision=18, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku_code"),
    )
    op.create_table(
        "supplier",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("supplier_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_code"),
    )
    op.create_table(
        "customer",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_code"),
    )
    op.create_table(
        "location",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("location_code", sa.String(length=64), nullable=False),
        sa.Column("zone", sa.String(length=32), nullable=True),
        sa.Column("aisle", sa.String(length=32), nullable=True),
        sa.Column("bin", sa.String(length=32), nullable=True),
        sa.Column(
            "space_status", sa.SmallInteger(), nullable=False, server_default="1"
        ),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "warehouse_id", "location_code", name="uq_location_wh_code"
        ),
    )


def downgrade() -> None:
    op.drop_table("location")
    op.drop_table("customer")
    op.drop_table("supplier")
    op.drop_table("sku")
