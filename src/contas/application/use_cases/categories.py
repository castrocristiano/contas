from typing import Any

from contas.application.ports.repositories import ICategoryRepository
from contas.domain.entities import Category
from contas.domain.enums import CategoryType
from contas.domain.errors import CategoryAlreadyExistsError
from contas.schemas.category import (
    CategoryResponse,
    CreateCategoryInput,
    ListCategoriesInput,
    ListCategoriesResponse,
)


class CreateCategoryUseCase:
    def __init__(self, category_repo: ICategoryRepository) -> None:
        self.category_repo = category_repo

    async def execute(self, payload: CreateCategoryInput) -> dict[str, Any]:
        existing = await self.category_repo.get_by_name(payload.name)
        if existing:
            raise CategoryAlreadyExistsError(payload.name)

        category = Category(
            name=payload.name,
            category_type=CategoryType(payload.category_type),
        )
        created = await self.category_repo.create(category)
        response = CategoryResponse(
            id=created.id,
            name=created.name,
            category_type=created.category_type,
            is_active=created.is_active,
        )
        return response.model_dump(mode="json")


class ListCategoriesUseCase:
    def __init__(self, category_repo: ICategoryRepository) -> None:
        self.category_repo = category_repo

    async def execute(self, payload: ListCategoriesInput) -> dict[str, Any]:
        categories = await self.category_repo.list_all(
            only_active=not payload.include_inactive,
            category_type=payload.category_type,
            limit=1000,
        )
        cat_responses = [
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                category_type=cat.category_type,
                is_active=cat.is_active,
            )
            for cat in categories
        ]
        response = ListCategoriesResponse(
            categories=cat_responses,
            count=len(cat_responses),
        )
        return response.model_dump(mode="json")
