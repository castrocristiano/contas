import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from contas.models.category import Category


class Budget(SQLModel, table=True):
    __tablename__ = "budget"
    __table_args__ = (
        UniqueConstraint("category_id", "month", "year", name="uq_budget_category_period"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category_id: uuid.UUID = Field(
        foreign_key="category.id",
        ondelete="RESTRICT",
        nullable=False,
        index=True,
    )
    amount: Decimal = Field(
        sa_type=Numeric(14, 2),
        max_digits=14,
        decimal_places=2,
        nullable=False,
    )
    month: int = Field(nullable=False, index=True)
    year: int = Field(nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    category: "Category" = Relationship(back_populates="budgets")

