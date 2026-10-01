from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from contas.application.container import get_container
from contas.domain.errors import ContasError, DatabaseError, IntegrityError
from contas.schemas.account import (
    CreateAccountInput,
    DeleteAccountInput,
    ListAccountsInput,
)


def register_account_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_account(payload: CreateAccountInput) -> dict:
        """Create a new financial account."""
        try:
            container = get_container()
            return await container.create_account_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def list_accounts(payload: ListAccountsInput) -> dict:
        """List accounts with their current balances and overall total."""
        try:
            container = get_container()
            return await container.list_accounts_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def delete_account(payload: DeleteAccountInput) -> dict:
        """Delete an account if it has no transactions, or deactivate it (soft-delete). If force_cascade is True, removes all related transactions and deletes the account."""
        try:
            container = get_container()
            return await container.delete_account_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
