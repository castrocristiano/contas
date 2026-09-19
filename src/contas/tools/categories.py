from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError, IntegrityError as SAIntegrityError
from sqlmodel import select

from contas.db.session import get_session
from contas.models.category import Category
from contas.schemas.category import (
    CategoryResponse,
    CreateCategoryInput,
    ListCategoriesInput,
    ListCategoriesResponse,
)
from contas.tools.errors import (
    CategoryAlreadyExistsError,
    ContasError,
    DatabaseError,
    IntegrityError,
)


def register_category_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_category(payload: CreateCategoryInput) -> dict:
        """Create a new category for financial transactions."""
        try:
            async with get_session() as session:
                existing = (
                    await session.exec(
                        select(Category).where(Category.name == payload.name)
                    )
                ).first()
                if existing:
                    raise CategoryAlreadyExistsError(payload.name)

                category = Category(
                    name=payload.name,
                    category_type=payload.category_type,
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)

            response = CategoryResponse(
                id=category.id,
                name=category.name,
                category_type=category.category_type,
                is_active=category.is_active,
            )
            return response.model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def list_categories(payload: ListCategoriesInput) -> dict:
        """List financial categories with optional filtering by type and activity status."""
        try:
            async with get_session() as session:
                query = select(Category)
                if not payload.include_inactive:
                    query = query.where(Category.is_active == True)
                if payload.category_type:
                    query = query.where(Category.category_type == payload.category_type)

                categories = (await session.exec(query.order_by(Category.name.asc()))).all()

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
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

