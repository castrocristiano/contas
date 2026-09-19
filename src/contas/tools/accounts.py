from decimal import Decimal

from mcp.server.mcpserver import MCPServer
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account
from contas.schemas.account import (
    AccountResponse,
    AccountSummary,
    CreateAccountInput,
    ListAccountsInput,
    ListAccountsResponse,
)


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

    @mcp.tool()
    async def list_accounts(payload: ListAccountsInput) -> dict:
        """List accounts with their current balances and overall total."""
        async with get_session() as session:
            query = select(Account)
            if not payload.include_inactive:
                query = query.where(Account.is_active == True)
            accounts = (await session.exec(query)).all()

        total = sum((acc.balance for acc in accounts), Decimal("0.00"))
        currency = accounts[0].currency if accounts else "BRL"

        summaries = [
            AccountSummary(
                id=acc.id,
                name=acc.name,
                account_type=acc.account_type,
                balance=f"{acc.balance:.2f}",
                currency=acc.currency,
                is_active=acc.is_active,
            )
            for acc in accounts
        ]

        response = ListAccountsResponse(
            accounts=summaries,
            total_balance=f"{total:.2f}",
            currency=currency,
            count=len(summaries),
        )
        return response.model_dump(mode="json")
