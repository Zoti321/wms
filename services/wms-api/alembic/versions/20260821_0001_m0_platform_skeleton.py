"""M0：角色/用户/仓库骨架与开发种子管理员。

Revision ID: 20260821_0001
Revises:
Create Date: 2026-08-21

开发种子账号（非生产）：
  username: admin
  password: Admin@123456
修改方式见 services/wms-api/README.md。
"""

from __future__ import annotations

import os
from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op

revision: str = "20260821_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_ADMIN_USERNAME = "admin"
SEED_ADMIN_PASSWORD = "Admin@123456"
SEED_ADMIN_ROLE_CODE = "admin"


def _should_seed_dev_admin() -> bool:
    """生产环境不写入默认口令；其它环境写入开发种子。"""
    env = os.environ.get("APP_ENV", "dev").lower()
    return env not in {"prod", "production"}


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "warehouse",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("warehouse_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("UTC_TIMESTAMP()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    if not _should_seed_dev_admin():
        return

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

    op.bulk_insert(
        roles,
        [{"id": 1, "code": SEED_ADMIN_ROLE_CODE, "name": "系统管理员"}],
    )
    password_hash = bcrypt.hashpw(
        SEED_ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")
    op.bulk_insert(
        users,
        [
            {
                "username": SEED_ADMIN_USERNAME,
                "password_hash": password_hash,
                "role_id": 1,
                "status": 1,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("warehouse")
    op.drop_table("roles")
