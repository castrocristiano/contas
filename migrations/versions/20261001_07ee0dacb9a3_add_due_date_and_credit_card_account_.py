"""add due_date and credit_card account type

Revision ID: 07ee0dacb9a3
Revises: b5f447bf6707
Create Date: 2026-10-01 14:49:31.481755

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "07ee0dacb9a3"
down_revision: str | Sequence[str] | None = "b5f447bf6707"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE account_type_enum ADD VALUE IF NOT EXISTS 'CREDIT_CARD'")
    op.execute("ALTER TYPE account_type_enum ADD VALUE IF NOT EXISTS 'credit_card'")
    op.add_column("transaction", sa.Column("due_date", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_transaction_due_date"), "transaction", ["due_date"], unique=False
    )
    op.execute(
        "UPDATE transaction SET due_date = transaction_date WHERE due_date IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_transaction_due_date"), table_name="transaction")
    op.drop_column("transaction", "due_date")
