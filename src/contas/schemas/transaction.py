from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contas.models.account import AccountType
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


class GetStatementInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID = Field(
        ...,
        description="UUID of the account to query",
    )
    start_date: str = Field(
        ...,
        description="Start of period. ISO 8601 date or datetime (e.g., '2026-09-01').",
    )
    end_date: str = Field(
        ...,
        description="End of period. ISO 8601 date or datetime (e.g., '2026-09-30').",
    )
    include_pending: bool = Field(
        default=False,
        description="If true, includes pending transactions. Default: false.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of transactions to return. Default: 50.",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "GetStatementInput":
        try:
            s_date = datetime.fromisoformat(self.start_date)
            e_date = datetime.fromisoformat(self.end_date)
        except ValueError as exc:
            raise ValueError(
                "start_date and end_date must be valid ISO 8601 strings"
            ) from exc

        if s_date > e_date:
            raise ValueError("start_date must be less than or equal to end_date")
        return self


class StatementAccountHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    current_balance: str


class StatementPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: str
    end: str


class StatementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    transaction_date: datetime
    description: str
    amount: str
    transaction_type: TransactionType
    status: TransactionStatus
    category: str | None = None


class StatementSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_income: str
    total_expense: str
    net: str
    count: int


class StatementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account: StatementAccountHeader
    period: StatementPeriod
    transactions: list[StatementItem]
    summary: StatementSummary


class GetFinancialSummaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_date: str | None = Field(
        default=None,
        description="Reference date for balance calculation. ISO 8601. Defaults to today.",
    )


class FinancialSummaryAccountItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    account_type: AccountType
    balance: str
    currency: str


class FinancialSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_date: str
    accounts: list[FinancialSummaryAccountItem]
    total_assets: str
    currency: str
