from datetime import UTC, datetime
from decimal import Decimal

from mcp.server.mcpserver import MCPServer
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account
from contas.models.category import Category
from contas.models.transaction import Transaction, TransactionType
from contas.schemas.transaction import (
    RecordTransactionInput,
    RecordTransactionResponse,
    SourceAccountSummary,
)


def register_transaction_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def record_transaction(payload: RecordTransactionInput) -> dict:
        """Record a financial transaction (income, expense, transfer) and atomically update balances."""
        amount = Decimal(payload.amount)

        parsed_date = datetime.now(UTC)
        if payload.transaction_date:
            parsed_date = datetime.fromisoformat(payload.transaction_date)

        async with get_session() as session:
            # 1. Validate source account
            source_account = (
                await session.exec(
                    select(Account).where(
                        Account.id == payload.source_account_id,
                        Account.is_active == True,
                    )
                )
            ).first()

            if not source_account:
                raise ValueError(
                    f"Active source account with ID '{payload.source_account_id}' not found."
                )

            # 2. Validate destination account if transfer
            destination_account: Account | None = None
            if payload.transaction_type == TransactionType.TRANSFER:
                destination_account = (
                    await session.exec(
                        select(Account).where(
                            Account.id == payload.destination_account_id,
                            Account.is_active == True,
                        )
                    )
                ).first()

                if not destination_account:
                    raise ValueError(
                        f"Active destination account with ID '{payload.destination_account_id}' not found."
                    )

            # 3. Validate category if provided
            if payload.category_id:
                category = (
                    await session.exec(
                        select(Category).where(
                            Category.id == payload.category_id,
                            Category.is_active == True,
                        )
                    )
                ).first()
                if not category:
                    raise ValueError(
                        f"Active category with ID '{payload.category_id}' not found."
                    )

            # 4. Atomic balance update
            if payload.transaction_type == TransactionType.EXPENSE:
                source_account.balance -= amount
            elif payload.transaction_type == TransactionType.INCOME:
                source_account.balance += amount
            elif payload.transaction_type == TransactionType.TRANSFER:
                source_account.balance -= amount
                assert destination_account is not None
                destination_account.balance += amount
                session.add(destination_account)

            session.add(source_account)

            # 5. Persist transaction
            transaction = Transaction(
                amount=amount,
                transaction_type=payload.transaction_type,
                status=payload.status,
                transaction_date=parsed_date,
                description=payload.description,
                source_account_id=payload.source_account_id,
                destination_account_id=payload.destination_account_id,
                category_id=payload.category_id,
            )
            session.add(transaction)

            await session.commit()
            await session.refresh(source_account)
            await session.refresh(transaction)

        response = RecordTransactionResponse(
            id=transaction.id,
            amount=f"{transaction.amount:.2f}",
            transaction_type=transaction.transaction_type,
            status=transaction.status,
            transaction_date=transaction.transaction_date,
            description=transaction.description,
            source_account=SourceAccountSummary(
                id=source_account.id,
                name=source_account.name,
                new_balance=f"{source_account.balance:.2f}",
            ),
            category_id=transaction.category_id,
            created_at=transaction.created_at,
        )
        return response.model_dump(mode="json")
