from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from contas.models.category import CategoryType


class CreateCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique name of the category (e.g., 'Alimentação', 'Salário')",
    )
    category_type: CategoryType = Field(
        ...,
        description="Type of the category: income or expense",
    )


class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    category_type: CategoryType
    is_active: bool


class ListCategoriesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_type: CategoryType | None = Field(
        default=None,
        description="Filter by category type (income or expense). Optional.",
    )
    include_inactive: bool = Field(
        default=False,
        description="If true, also includes inactive categories. Default: false.",
    )


class ListCategoriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[CategoryResponse]
    count: int
