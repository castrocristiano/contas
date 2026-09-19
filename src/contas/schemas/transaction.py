from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contas.models.transaction import TransactionStatus, TransactionType


class SourceAccountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    new_balance: str


class RecordTransactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    amount: str = Field(
        ...,
        description="Transaction amount as a positive decimal string (e.g., '35.50'). Must be > 0.",
        pattern=r"^[0-9]+(\.[0-9]{1,2})?$",
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of transaction: income, expense, transfer",
    )
    source_account_id: UUID = Field(
        ...,
        description="UUID of the source (debit) account",
    )
    destination_account_id: UUID | None = Field(
        default=None,
        description="UUID of the destination (credit) account. Required when transaction_type is 'transfer'.",
    )
    category_id: UUID | None = Field(
        default=None,
        description="UUID of the category. Optional.",
    )
    description: str = Field(
        default="",
        max_length=255,
        description="Short description of the transaction",
    )
    transaction_date: str | None = Field(
        default=None,
        description="ISO 8601 datetime with timezone (e.g., '2026-09-19T14:00:00-03:00'). Defaults to current time.",
    )
    status: TransactionStatus = Field(
        default=TransactionStatus.CLEARED,
        description="Settlement status. 'pending' for scheduled future transactions.",
    )

    @model_validator(mode="after")
    def validate_transaction(self) -> "RecordTransactionInput":
        try:
            val = Decimal(self.amount)
        except Exception as exc:
            raise ValueError("Amount must be a valid decimal number") from exc

        if val <= 0:
            raise ValueError("Amount must be greater than 0")

        if self.transaction_type == TransactionType.TRANSFER:
            if not self.destination_account_id:
                raise ValueError(
                    "destination_account_id is required when transaction_type is 'transfer'"
                )
            if self.destination_account_id == self.source_account_id:
                raise ValueError(
                    "destination_account_id must be different from source_account_id"
                )

        return self


class RecordTransactionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    amount: str
    transaction_type: TransactionType
    status: TransactionStatus
    transaction_date: datetime
    description: str
    source_account: SourceAccountSummary
    category_id: UUID | None = None
    created_at: datetime
