from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from contas.models.account import AccountType


class CreateAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the account (e.g., 'Checking Account', 'Carteira')",
    )
    account_type: AccountType = Field(
        ...,
        description="Type of account: checking, savings, investment, cash",
    )
    initial_balance: str = Field(
        default="0.00",
        description="Opening balance as a decimal string (e.g., '1500.00'). Defaults to '0.00'.",
    )
    currency: str = Field(
        default="BRL",
        description="Three-letter ISO 4217 currency code",
        pattern=r"^[A-Z]{3}$",
    )


class AccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    account_type: AccountType
    balance: str
    currency: str
    is_active: bool
    created_at: datetime


class AccountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    account_type: AccountType
    balance: str
    currency: str
    is_active: bool


class ListAccountsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_inactive: bool = Field(
        default=False,
        description="If true, also returns inactive accounts. Default: false.",
    )


class ListAccountsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: list[AccountSummary]
    total_balance: str
    currency: str
    count: int


class DeleteAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID = Field(
        ...,
        description="UUID of the account to delete or deactivate.",
    )
    force_cascade: bool = Field(
        default=False,
        description="If true, removes the account and all related transactions. If false and transactions exist, deactivates the account.",
    )


class DeleteAccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    name: str
    action_taken: str  # "deleted" | "deactivated"
    message: str
