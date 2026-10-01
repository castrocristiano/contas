from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from contas.application.container import get_container
from contas.domain.errors import ContasError, DatabaseError, IntegrityError
from contas.schemas.budget import (
    GetBudgetStatusInput,
    SetBudgetInput,
)


def register_budget_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def set_budget(payload: SetBudgetInput) -> dict:
        """Set or update a monthly budget limit for an expense category."""
        try:
            container = get_container()
            return await container.set_budget_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_budget_status(payload: GetBudgetStatusInput) -> dict:
        """Get budget execution and consumption metrics for a specific month and year."""
        try:
            container = get_container()
            return await container.get_budget_status_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
