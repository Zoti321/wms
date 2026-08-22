"""M6：角色种子、操作日志与基础字典。

Revision ID: 20260821_0007
Revises: 20260821_0006
Create Date: 2026-08-22
"""

from __future__ import annotations

import os
from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0007"
down_revision: Union[str, Sequence[str], None] = "20260821_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_PASSWORD = "Admin@123456"


def _should_seed() -> bool:
    env = os.environ.get("APP_ENV", "dev").lower()
    return env not in {"prod", "production"}


def upgrade() -> None:
    op.create_table(
        "operation_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column("operator_name", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operation_log_operator_id", "operation_log", ["operator_id"])
    op.create_index("ix_operation_log_created_at", "operation_log", ["created_at"])

    op.create_table(
        "dict_item",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dict_type", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dict_type", "code", name="uq_dict_item_type_code"),
    )

    if not _should_seed():
        return

    conn = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.BigInteger),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
    )
    users = sa.table(
        "users",
        sa.column("username", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("role_id", sa.BigInteger),
        sa.column("status", sa.SmallInteger),
    )
    dict_item = sa.table(
        "dict_item",
        sa.column("dict_type", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("status", sa.SmallInteger),
    )

    existing = {
        row[0]
        for row in conn.execute(sa.text("SELECT code FROM roles")).fetchall()
    }
    role_rows = [
        {"code": "supervisor", "name": "仓库主管"},
        {"code": "operator", "name": "仓管员"},
        {"code": "viewer", "name": "采购/业务只读"},
    ]
    for row in role_rows:
        if row["code"] not in existing:
            conn.execute(
                roles.insert().values(code=row["code"], name=row["name"])
            )

    role_ids = {
        row[0]: row[1]
        for row in conn.execute(sa.text("SELECT code, id FROM roles")).fetchall()
    }
    password_hash = bcrypt.hashpw(
        SEED_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")
    existing_users = {
        row[0]
        for row in conn.execute(sa.text("SELECT username FROM users")).fetchall()
    }
    for username, role_code in (
        ("supervisor", "supervisor"),
        ("operator", "operator"),
        ("viewer", "viewer"),
    ):
        if username in existing_users:
            continue
        conn.execute(
            users.insert().values(
                username=username,
                password_hash=password_hash,
                role_id=role_ids[role_code],
                status=1,
            )
        )

    op.bulk_insert(
        dict_item,
        [
            {"dict_type": "unit", "code": "PCS", "name": "件", "sort_order": 1, "status": 1},
            {"dict_type": "unit", "code": "BOX", "name": "箱", "sort_order": 2, "status": 1},
            {
                "dict_type": "inbound_order_type",
                "code": "purchase",
                "name": "采购入库",
                "sort_order": 1,
                "status": 1,
            },
            {
                "dict_type": "inbound_order_type",
                "code": "return",
                "name": "退货入库",
                "sort_order": 2,
                "status": 1,
            },
            {
                "dict_type": "cancel_reason",
                "code": "customer_cancel",
                "name": "客户取消",
                "sort_order": 1,
                "status": 1,
            },
            {
                "dict_type": "cancel_reason",
                "code": "stock_shortage",
                "name": "库存不足",
                "sort_order": 2,
                "status": 1,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("dict_item")
    op.drop_index("ix_operation_log_created_at", table_name="operation_log")
    op.drop_index("ix_operation_log_operator_id", table_name="operation_log")
    op.drop_table("operation_log")
