from datetime import UTC, datetime
from decimal import Decimal

from mcp.server.mcpserver import MCPServer
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account
from contas.models.category import Category
from contas.models.transaction import Transaction, TransactionStatus, TransactionType
from contas.schemas.transaction import (
    FinancialSummaryAccountItem,
    FinancialSummaryResponse,
    GetFinancialSummaryInput,
    GetStatementInput,
    RecordTransactionInput,
    RecordTransactionResponse,
    SourceAccountSummary,
    StatementAccountHeader,
    StatementItem,
    StatementPeriod,
    StatementResponse,
    StatementSummary,
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

    @mcp.tool()
    async def get_statement(payload: GetStatementInput) -> dict:
        """Get the detailed statement of an account for a given period."""
        s_date = datetime.fromisoformat(payload.start_date)
        e_date = datetime.fromisoformat(payload.end_date)

        async with get_session() as session:
            account = (
                await session.exec(
                    select(Account).where(Account.id == payload.account_id)
                )
            ).first()
            if not account:
                raise ValueError(
                    f"Account with ID '{payload.account_id}' was not found."
                )

            query = select(Transaction).where(
                Transaction.source_account_id == payload.account_id,
                Transaction.transaction_date >= s_date,
                Transaction.transaction_date <= e_date,
            )
            if not payload.include_pending:
                query = query.where(Transaction.status == TransactionStatus.CLEARED)

            query = query.order_by(Transaction.transaction_date.asc()).limit(
                payload.limit
            )
            transactions = (await session.exec(query)).all()

            total_income = Decimal("0.00")
            total_expense = Decimal("0.00")
            items: list[StatementItem] = []

            for tx in transactions:
                if tx.transaction_type == TransactionType.INCOME:
                    total_income += tx.amount
                elif tx.transaction_type in (
                    TransactionType.EXPENSE,
                    TransactionType.TRANSFER,
                ):
                    total_expense += tx.amount

                category_name = None
                if tx.category_id:
                    cat = (
                        await session.exec(
                            select(Category).where(Category.id == tx.category_id)
                        )
                    ).first()
                    if cat:
                        category_name = cat.name

                items.append(
                    StatementItem(
                        id=tx.id,
                        transaction_date=tx.transaction_date,
                        description=tx.description,
                        amount=f"{tx.amount:.2f}",
                        transaction_type=tx.transaction_type,
                        status=tx.status,
                        category=category_name,
                    )
                )

            net = total_income - total_expense

            response = StatementResponse(
                account=StatementAccountHeader(
                    id=account.id,
                    name=account.name,
                    current_balance=f"{account.balance:.2f}",
                ),
                period=StatementPeriod(
                    start=payload.start_date,
                    end=payload.end_date,
                ),
                transactions=items,
                summary=StatementSummary(
                    total_income=f"{total_income:.2f}",
                    total_expense=f"{total_expense:.2f}",
                    net=f"{net:.2f}",
                    count=len(items),
                ),
            )
            return response.model_dump(mode="json")

    @mcp.tool()
    async def get_financial_summary(payload: GetFinancialSummaryInput) -> dict:
        """Get consolidated financial summary of all active accounts."""
        ref_date = payload.reference_date or datetime.now(UTC).date().isoformat()

        async with get_session() as session:
            accounts = (
                await session.exec(select(Account).where(Account.is_active == True))
            ).all()

        total = sum((acc.balance for acc in accounts), Decimal("0.00"))
        currency = accounts[0].currency if accounts else "BRL"

        account_items = [
            FinancialSummaryAccountItem(
                id=acc.id,
                name=acc.name,
                account_type=acc.account_type,
                balance=f"{acc.balance:.2f}",
                currency=acc.currency,
            )
            for acc in accounts
        ]

        response = FinancialSummaryResponse(
            reference_date=ref_date,
            accounts=account_items,
            total_assets=f"{total:.2f}",
            currency=currency,
        )
        return response.model_dump(mode="json")
