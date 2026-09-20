from decimal import Decimal

from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account
from contas.models.transaction import Transaction
from contas.schemas.account import (
    AccountResponse,
    AccountSummary,
    CreateAccountInput,
    DeleteAccountInput,
    DeleteAccountResponse,
    ListAccountsInput,
    ListAccountsResponse,
)
from contas.tools.errors import (
    AccountNotFoundError,
    ContasError,
    DatabaseError,
    IntegrityError,
)


def register_account_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_account(payload: CreateAccountInput) -> dict:
        """Create a new financial account."""
        try:
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
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def delete_account(payload: DeleteAccountInput) -> dict:
        """Delete an account if it has no transactions, or deactivate it (soft-delete). If force_cascade is True, removes all related transactions and deletes the account."""
        try:
            async with get_session() as session, session.begin():
                account = (
                    await session.exec(
                        select(Account).where(Account.id == payload.account_id)
                    )
                ).first()
                if not account:
                    raise AccountNotFoundError(str(payload.account_id))

                # Check for existing transactions
                tx_stmt = select(Transaction).where(
                    (Transaction.source_account_id == payload.account_id)
                    | (Transaction.destination_account_id == payload.account_id)
                )
                transactions = (await session.exec(tx_stmt)).all()

                if transactions and not payload.force_cascade:
                    # Soft-delete (deactivate)
                    account.is_active = False
                    session.add(account)
                    action_taken = "deactivated"
                    message = f"Account '{account.name}' has {len(transactions)} transaction(s) and was deactivated."
                else:
                    # Delete transactions if forced
                    if transactions and payload.force_cascade:
                        for tx in transactions:
                            await session.delete(tx)

                    await session.delete(account)
                    action_taken = "deleted"
                    message = f"Account '{account.name}' was permanently deleted."

            return DeleteAccountResponse(
                account_id=payload.account_id,
                name=account.name,
                action_taken=action_taken,
                message=message,
            ).model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
