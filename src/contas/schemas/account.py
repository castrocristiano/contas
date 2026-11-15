from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from contas.models.account import AccountType

_OWNER_USER_DESC = "ID of the owner user (multi-tenant context)."


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
    user_id: UUID | None = Field(
        default=None,
        description=_OWNER_USER_DESC,
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
    user_id: UUID | None = None


class AccountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    account_type: AccountType
    balance: str
    currency: str
    is_active: bool
    user_id: UUID | None = None


class ListAccountsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_inactive: bool = Field(
        default=False,
        description="Whether to include inactive/deactivated accounts. Defaults to False.",
    )
    user_id: UUID | None = Field(
        default=None,
        description="Filter accounts by owner user ID.",
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
    user_id: UUID | None = Field(
        default=None,
        description=_OWNER_USER_DESC,
    )


class DeleteAccountResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    name: str
    action_taken: str  # "deleted" | "deactivated"
    message: str


class UpdateAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    account_id: UUID = Field(
        ...,
        description="UUID of the account to update.",
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New display name of the account.",
    )
    is_active: bool | None = Field(
        default=None,
        description="Active status of the account.",
    )
    user_id: UUID | None = Field(
        default=None,
        description=_OWNER_USER_DESC,
    )


class AccountBalanceProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: UUID
    account_name: str
    account_type: str
    current_balance: str
    pending_income: str
    pending_expense: str
    pending_transfers_net: str
    projected_balance: str
    is_projected_negative: bool


class GetDashboardProjectionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID | None = Field(
        default=None,
        description=_OWNER_USER_DESC,
    )
    until_date: str | None = Field(
        default=None,
        description="Horizon date for pending transactions (ISO 8601 YYYY-MM-DD). Defaults to end of current month.",
    )


class DashboardProjectionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_date: str
    total_current_balance: str
    total_pending_income: str
    total_pending_expense: str
    total_projected_balance: str
    accounts: list[AccountBalanceProjection]
