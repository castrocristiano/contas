from decimal import Decimal

from mcp.server.mcpserver import MCPServer

from contas.db.session import get_session
from contas.models.account import Account
from contas.schemas.account import AccountResponse, CreateAccountInput


def register_account_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_account(payload: CreateAccountInput) -> dict:
        """Create a new financial account."""
        initial_balance = Decimal(payload.initial_balance)
        account = Account(
            name=payload.name,
            account_type=payload.account_type,
            balance=initial_balance,
            currency=payload.currency,
        )

        async with get_session() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)

        response = AccountResponse(
            id=account.id,
            name=account.name,
            account_type=account.account_type,
            balance=f"{account.balance:.2f}",
            currency=account.currency,
            is_active=account.is_active,
            created_at=account.created_at,
        )
        return response.model_dump(mode="json")
