"""补充 outbound_order_type 与 inbound other 字典种子。

Revision ID: 20260823_0008
Revises: 20260821_0007
Create Date: 2026-08-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0008"
down_revision: Union[str, Sequence[str], None] = "20260821_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEEDS = (
    ("inbound_order_type", "other", "其他入库", 3),
    ("outbound_order_type", "sales", "销售出库", 1),
    ("outbound_order_type", "material", "领料出库", 2),
    ("outbound_order_type", "other", "其他出库", 3),
)


def upgrade() -> None:
    conn = op.get_bind()
    for dict_type, code, name, sort_order in _SEEDS:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM dict_item WHERE dict_type=:t AND code=:c LIMIT 1"
            ),
            {"t": dict_type, "c": code},
        ).first()
        if exists:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO dict_item (dict_type, code, name, sort_order, status) "
                "VALUES (:t, :c, :n, :s, 1)"
            ),
            {"t": dict_type, "c": code, "n": name, "s": sort_order},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for dict_type, code, _, _ in _SEEDS:
        conn.execute(
            sa.text("DELETE FROM dict_item WHERE dict_type=:t AND code=:c"),
            {"t": dict_type, "c": code},
        )
