"""add user_id to orders

Revision ID: 5eca0482f8df
Revises: 14ab99729d7a
Create Date: 2026-09-14 00:31:33.985038

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5eca0482f8df'
down_revision: Union[str, None] = '14ab99729d7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )

        batch_op.create_foreign_key(
            "fk_orders_user_id",
            "users",
            ["user_id"],
            ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_orders_user_id",
            type_="foreignkey"
        )

        batch_op.drop_column("user_id")
