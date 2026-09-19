import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from contas.models.budget import Budget
    from contas.models.transaction import Transaction


class CategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100, nullable=False)
    category_type: CategoryType = Field(
        sa_column=Column(
            sa.Enum(CategoryType, name="category_type_enum", native_enum=True),
            nullable=False,
        )
    )
    is_active: bool = Field(default=True, nullable=False)

    transactions: list["Transaction"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    budgets: list["Budget"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"passive_deletes": True},
    )
