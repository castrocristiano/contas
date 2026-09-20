from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account
from contas.models.category import Category
from contas.models.transaction import Transaction, TransactionStatus, TransactionType
from contas.schemas.transaction import (
    DeleteTransactionInput,
    DeleteTransactionResponse,
    FinancialSummaryAccountItem,
    FinancialSummaryResponse,
    GetFinancialSummaryInput,
    GetInstallmentPlanInput,
    GetStatementInput,
    InstallmentItemResponse,
    InstallmentPlanResponse,
    RecordTransactionInput,
    RecordTransactionResponse,
    SourceAccountSummary,
    StatementAccountHeader,
    StatementItem,
    StatementPeriod,
    StatementResponse,
    StatementSummary,
)
from contas.tools.errors import (
    AccountNotFoundError,
    CategoryNotFoundError,
    ContasError,
    DatabaseError,
    InstallmentPlanNotFoundError,
    IntegrityError,
    TransactionNotFoundError,
    TransferSameAccountError,
)
from contas.utils.installments import add_months, calculate_installments


def register_transaction_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def record_transaction(payload: RecordTransactionInput) -> dict:
        """Record a financial transaction (income, expense, transfer, or installment purchase) and atomically update balances."""
        try:
            if (
                payload.transaction_type == TransactionType.TRANSFER
                and payload.source_account_id == payload.destination_account_id
            ):
                raise TransferSameAccountError(str(payload.source_account_id))

            amount = Decimal(payload.amount)

            parsed_date = datetime.now(UTC)
            if payload.transaction_date:
                parsed_date = datetime.fromisoformat(payload.transaction_date)

            # Determine installment parameters
            is_installment = (
                payload.total_installments is not None
                and payload.total_installments > 1
            )
            installment_id = uuid4() if is_installment else None
            installment_amounts: list[Decimal] = []

            if is_installment:
                total_installments = payload.total_installments
                assert total_installments is not None

                total_amount = (
                    Decimal(payload.total_amount) if payload.total_amount else amount
                )
                installment_amounts = calculate_installments(
                    total_amount, total_installments
                )
                first_installment_amount = installment_amounts[0]
            else:
                total_installments = payload.total_installments
                total_amount = (
                    Decimal(payload.total_amount) if payload.total_amount else None
                )
                first_installment_amount = amount

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
                    raise AccountNotFoundError(
                        str(payload.source_account_id), field="source_account_id"
                    )

                # 2. Validate destination account if transfer
                destination_account: Account | None = None
                if payload.transaction_type == TransactionType.TRANSFER:
                    assert payload.destination_account_id is not None
                    destination_account = (
                        await session.exec(
                            select(Account).where(
                                Account.id == payload.destination_account_id,
                                Account.is_active == True,
                            )
                        )
                    ).first()

                    if not destination_account:
                        raise AccountNotFoundError(
                            str(payload.destination_account_id),
                            field="destination_account_id",
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
                        raise CategoryNotFoundError(str(payload.category_id))

                # 4. Atomic balance update (only first installment if cleared)
                if payload.status == TransactionStatus.CLEARED:
                    if payload.transaction_type == TransactionType.EXPENSE:
                        source_account.balance -= first_installment_amount
                    elif payload.transaction_type == TransactionType.INCOME:
                        source_account.balance += first_installment_amount
                    elif payload.transaction_type == TransactionType.TRANSFER:
                        source_account.balance -= first_installment_amount
                        assert destination_account is not None
                        destination_account.balance += first_installment_amount
                        session.add(destination_account)

                    session.add(source_account)

                # 5. Persist first transaction
                transaction = Transaction(
                    amount=first_installment_amount,
                    transaction_type=payload.transaction_type,
                    status=payload.status,
                    transaction_date=parsed_date,
                    description=payload.description,
                    source_account_id=payload.source_account_id,
                    destination_account_id=payload.destination_account_id,
                    category_id=payload.category_id,
                    installment_id=installment_id,
                    installment_number=1
                    if is_installment
                    else payload.installment_number,
                    total_installments=total_installments,
                    total_amount=total_amount,
                )
                session.add(transaction)

                # 6. If installment, persist subsequent installments with status=PENDING
                if is_installment:
                    for idx, inst_amount in enumerate(installment_amounts[1:], start=2):
                        inst_date = add_months(parsed_date, idx - 1)
                        sub_tx = Transaction(
                            amount=inst_amount,
                            transaction_type=payload.transaction_type,
                            status=TransactionStatus.PENDING,
                            transaction_date=inst_date,
                            description=payload.description,
                            source_account_id=payload.source_account_id,
                            destination_account_id=payload.destination_account_id,
                            category_id=payload.category_id,
                            installment_id=installment_id,
                            installment_number=idx,
                            total_installments=total_installments,
                            total_amount=total_amount,
                        )
                        session.add(sub_tx)

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
                installment_id=transaction.installment_id,
                installment_number=transaction.installment_number,
                total_installments=transaction.total_installments,
                total_amount=f"{transaction.total_amount:.2f}"
                if transaction.total_amount is not None
                else None,
                created_at=transaction.created_at,
            )
            return response.model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_statement(payload: GetStatementInput) -> dict:
        """Get the detailed statement of an account for a given period."""
        try:
            s_date = datetime.fromisoformat(payload.start_date)
            e_date = datetime.fromisoformat(payload.end_date)

            async with get_session() as session:
                account = (
                    await session.exec(
                        select(Account).where(Account.id == payload.account_id)
                    )
                ).first()
                if not account:
                    raise AccountNotFoundError(str(payload.account_id))

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
                            installment_id=tx.installment_id,
                            installment_number=tx.installment_number,
                            total_installments=tx.total_installments,
                            total_amount=f"{tx.total_amount:.2f}"
                            if tx.total_amount is not None
                            else None,
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
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_installment_plan(payload: GetInstallmentPlanInput) -> dict:
        """Get the full installment plan and schedule for a given installment purchase ID."""
        try:
            async with get_session() as session:
                query = (
                    select(Transaction)
                    .where(Transaction.installment_id == payload.installment_id)
                    .order_by(Transaction.installment_number.asc())
                )
                transactions = (await session.exec(query)).all()

            if not transactions:
                raise InstallmentPlanNotFoundError(str(payload.installment_id))

            first_tx = transactions[0]
            total_amount = first_tx.total_amount or sum(
                (t.amount for t in transactions), Decimal("0.00")
            )
            total_installments = first_tx.total_installments or len(transactions)

            paid_amount = Decimal("0.00")
            paid_count = 0
            remaining_amount = Decimal("0.00")
            remaining_count = 0

            items: list[InstallmentItemResponse] = []
            for tx in transactions:
                if tx.status == TransactionStatus.CLEARED:
                    paid_amount += tx.amount
                    paid_count += 1
                else:
                    remaining_amount += tx.amount
                    remaining_count += 1

                items.append(
                    InstallmentItemResponse(
                        id=tx.id,
                        installment_number=tx.installment_number or 0,
                        amount=f"{tx.amount:.2f}",
                        due_date=tx.transaction_date,
                        status=tx.status,
                    )
                )

            response = InstallmentPlanResponse(
                installment_id=payload.installment_id,
                description=first_tx.description,
                account_id=first_tx.source_account_id,
                category_id=first_tx.category_id,
                total_amount=f"{total_amount:.2f}",
                total_installments=total_installments,
                paid_amount=f"{paid_amount:.2f}",
                remaining_amount=f"{remaining_amount:.2f}",
                paid_installments=paid_count,
                remaining_installments=remaining_count,
                installments=items,
            )
            return response.model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_financial_summary(payload: GetFinancialSummaryInput) -> dict:
        """Get consolidated financial summary of all active accounts."""
        try:
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
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def delete_transaction(payload: DeleteTransactionInput) -> dict:
        """Delete a transaction, reverting any cleared amounts to account balances atomically, with support for deleting individual installments or all installments in a plan."""
        try:
            async with get_session() as session, session.begin():
                tx = (
                    await session.exec(
                        select(Transaction).where(
                            Transaction.id == payload.transaction_id
                        )
                    )
                ).first()
                if not tx:
                    raise TransactionNotFoundError(str(payload.transaction_id))

                transactions_to_delete: list[Transaction] = []
                if payload.delete_all_installments and tx.installment_id is not None:
                    stmt = select(Transaction).where(
                        Transaction.installment_id == tx.installment_id
                    )
                    transactions_to_delete = (await session.exec(stmt)).all()
                else:
                    transactions_to_delete = [tx]

                reverted_total = Decimal("0.00")

                # Revert balances for cleared transactions
                for item in transactions_to_delete:
                    if item.status == TransactionStatus.CLEARED:
                        source_account = await session.get(
                            Account, item.source_account_id
                        )
                        if source_account:
                            if item.transaction_type == TransactionType.EXPENSE:
                                source_account.balance += item.amount
                                reverted_total += item.amount
                            elif item.transaction_type == TransactionType.INCOME:
                                source_account.balance -= item.amount
                                reverted_total += item.amount
                            elif item.transaction_type == TransactionType.TRANSFER:
                                source_account.balance += item.amount
                                reverted_total += item.amount
                                if item.destination_account_id:
                                    dest_account = await session.get(
                                        Account, item.destination_account_id
                                    )
                                    if dest_account:
                                        dest_account.balance -= item.amount
                                        session.add(dest_account)
                            session.add(source_account)

                    await session.delete(item)

            count = len(transactions_to_delete)
            return DeleteTransactionResponse(
                transaction_id=payload.transaction_id,
                deleted_count=count,
                reverted_amount=f"{reverted_total:.2f}",
                message=f"Successfully deleted {count} transaction(s) and reverted R$ {reverted_total:.2f}.",
            ).model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
