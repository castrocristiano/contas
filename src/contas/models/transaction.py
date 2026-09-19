import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from contas.models.account import Account
from contas.models.category import Category


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    CLEARED = "cleared"
    PENDING = "pending"


class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    amount: Decimal = Field(
        sa_type=Numeric(14, 2),
        max_digits=14,
        decimal_places=2,
        nullable=False,
    )
    transaction_type: TransactionType = Field(
        sa_column=Column(
            sa.Enum(TransactionType, name="transaction_type_enum", native_enum=True),
            nullable=False,
        )
    )
    status: TransactionStatus = Field(
        default=TransactionStatus.CLEARED,
        sa_column=Column(
            sa.Enum(
                TransactionStatus, name="transaction_status_enum", native_enum=True
            ),
            nullable=False,
        ),
    )
    transaction_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    description: str = Field(default="", max_length=255, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    source_account_id: uuid.UUID = Field(
        foreign_key="account.id",
        ondelete="RESTRICT",
        nullable=False,
        index=True,
    )
    destination_account_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="account.id",
        ondelete="RESTRICT",
        nullable=True,
        index=True,
    )
    category_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="category.id",
        ondelete="RESTRICT",
        nullable=True,
        index=True,
    )

    source_account: Account = Relationship(
        back_populates="outgoing_transactions",
        sa_relationship_kwargs={"foreign_keys": [source_account_id]},
    )
    destination_account: Account | None = Relationship(
        back_populates="incoming_transactions",
        sa_relationship_kwargs={"foreign_keys": [destination_account_id]},
    )
    category: Category | None = Relationship(back_populates="transactions")
