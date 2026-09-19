from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SetBudgetInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category_id: UUID = Field(
        ...,
        description="UUID of the expense category",
    )
    amount: str = Field(
        ...,
        description="Monthly budget limit as a decimal string (e.g., '500.00'). Must be > 0.",
        pattern=r"^[0-9]+(\.[0-9]{1,2})?$",
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month number (1 to 12)",
    )
    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Year (e.g., 2026)",
    )

    @field_validator("amount")
    @classmethod
    def validate_amount_gt_zero(cls, value: str) -> str:
        dec = Decimal(value)
        if dec <= 0:
            raise ValueError("amount must be greater than zero")
        return value


class BudgetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    category_id: UUID
    category_name: str
    amount: str
    month: int
    year: int
    created_at: datetime


class GetBudgetStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Month number (1 to 12). Defaults to current month.",
    )
    year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
        description="Year (e.g., 2026). Defaults to current year.",
    )
    category_id: UUID | None = Field(
        default=None,
        description="Filter by specific category UUID. Optional.",
    )


class BudgetItemStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID
    category_name: str
    budget_amount: str
    spent_amount: str
    remaining_balance: str
    spent_percentage: str
    is_exceeded: bool


class BudgetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_budgeted: str
    total_spent: str
    total_remaining: str
    overall_percentage: str


class BudgetPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month: int
    year: int


class BudgetStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: BudgetPeriod
    budgets: list[BudgetItemStatus]
    summary: BudgetSummary
