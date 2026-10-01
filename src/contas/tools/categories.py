from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from contas.application.container import get_container
from contas.domain.errors import ContasError, DatabaseError, IntegrityError
from contas.schemas.category import (
    CreateCategoryInput,
    ListCategoriesInput,
)


def register_category_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_category(payload: CreateCategoryInput) -> dict:
        """Create a new category for financial transactions."""
        try:
            container = get_container()
            return await container.create_category_uc.execute(payload)
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
            container = get_container()
            return await container.list_categories_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
