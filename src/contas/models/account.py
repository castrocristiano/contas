import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from contas.models.transaction import Transaction


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CASH = "cash"


class Account(SQLModel, table=True):
    __tablename__ = "account"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, max_length=100, nullable=False)
    account_type: AccountType = Field(
        sa_column=Column(
            sa.Enum(AccountType, name="account_type_enum", native_enum=True),
            nullable=False,
        )
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(14, 2),
        max_digits=14,
        decimal_places=2,
        nullable=False,
    )
    currency: str = Field(default="BRL", max_length=3, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    outgoing_transactions: list["Transaction"] = Relationship(
        back_populates="source_account",
        sa_relationship_kwargs={
            "foreign_keys": "Transaction.source_account_id",
            "passive_deletes": True,
        },
    )
    incoming_transactions: list["Transaction"] = Relationship(
        back_populates="destination_account",
        sa_relationship_kwargs={
            "foreign_keys": "Transaction.destination_account_id",
            "passive_deletes": True,
        },
    )
