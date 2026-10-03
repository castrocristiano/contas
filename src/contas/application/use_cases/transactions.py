from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from contas.application.ports.repositories import (
    IAccountRepository,
    ICategoryRepository,
    ITransactionRepository,
)
from contas.domain.entities import Transaction
from contas.domain.enums import TransactionStatus, TransactionType
from contas.domain.errors import (
    AccountNotFoundError,
    CategoryNotFoundError,
    InstallmentPlanNotFoundError,
    TransactionNotFoundError,
    TransferSameAccountError,
)
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
from contas.utils.installments import add_months, calculate_installments


class RecordTransactionUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
        category_repo: ICategoryRepository,
    ) -> None:
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    async def execute(self, payload: RecordTransactionInput) -> dict[str, Any]:
        if (
            payload.transaction_type == TransactionType.TRANSFER
            and payload.source_account_id == payload.destination_account_id
        ):
            raise TransferSameAccountError(str(payload.source_account_id))

        amount = Decimal(payload.amount)
        parsed_date = datetime.now(UTC)
        if payload.transaction_date:
            parsed_date = datetime.fromisoformat(payload.transaction_date)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=UTC)

        parsed_due_date = parsed_date
        if payload.due_date:
            parsed_due_date = datetime.fromisoformat(payload.due_date)
            if parsed_due_date.tzinfo is None:
                parsed_due_date = parsed_due_date.replace(tzinfo=UTC)

        is_installment = (
            payload.total_installments is not None and payload.total_installments > 1
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

        # 1. Validate source account
        source_account = await self.account_repo.get_by_id(
            payload.source_account_id, user_id=payload.user_id, only_active=True
        )
        if not source_account:
            raise AccountNotFoundError(
                str(payload.source_account_id), field="source_account_id"
            )

        tx_user_id = payload.user_id or source_account.user_id

        # 2. Validate destination account
        destination_account = None
        if payload.transaction_type == TransactionType.TRANSFER:
            assert payload.destination_account_id is not None
            destination_account = await self.account_repo.get_by_id(
                payload.destination_account_id,
                user_id=payload.user_id,
                only_active=True,
            )
            if not destination_account:
                raise AccountNotFoundError(
                    str(payload.destination_account_id), field="destination_account_id"
                )

        # 3. Validate category
        if payload.category_id:
            category = await self.category_repo.get_by_id(
                payload.category_id, user_id=payload.user_id, only_active=True
            )
            if not category:
                raise CategoryNotFoundError(str(payload.category_id))

        # 4. Atomic balance update
        if payload.status == TransactionStatus.CLEARED:
            if payload.transaction_type == TransactionType.EXPENSE:
                source_account.balance -= first_installment_amount
            elif payload.transaction_type == TransactionType.INCOME:
                source_account.balance += first_installment_amount
            elif payload.transaction_type == TransactionType.TRANSFER:
                source_account.balance -= first_installment_amount
                assert destination_account is not None
                destination_account.balance += first_installment_amount
                await self.account_repo.update(destination_account)

            await self.account_repo.update(source_account)

        # 5. Persist first transaction
        transaction = Transaction(
            amount=first_installment_amount,
            transaction_type=TransactionType(payload.transaction_type),
            status=TransactionStatus(payload.status),
            transaction_date=parsed_date,
            due_date=parsed_due_date,
            description=payload.description,
            source_account_id=payload.source_account_id,
            destination_account_id=payload.destination_account_id,
            category_id=payload.category_id,
            user_id=tx_user_id,
            installment_id=installment_id,
            installment_number=1 if is_installment else payload.installment_number,
            total_installments=total_installments,
        )
        created_tx = await self.transaction_repo.create(transaction)

        # 6. If installment, persist subsequent installments
        if is_installment:
            sub_txs = []
            for idx, inst_amount in enumerate(installment_amounts[1:], start=2):
                inst_date = add_months(parsed_date, idx - 1)
                inst_due_date = add_months(parsed_due_date, idx - 1)
                sub_txs.append(
                    Transaction(
                        amount=inst_amount,
                        transaction_type=TransactionType(payload.transaction_type),
                        status=TransactionStatus.PENDING,
                        transaction_date=inst_date,
                        due_date=inst_due_date,
                        description=payload.description,
                        source_account_id=payload.source_account_id,
                        destination_account_id=payload.destination_account_id,
                        category_id=payload.category_id,
                        user_id=tx_user_id,
                        installment_id=installment_id,
                        installment_number=idx,
                        total_installments=total_installments,
                    )
                )
            await self.transaction_repo.create_many(sub_txs)

        response = RecordTransactionResponse(
            id=created_tx.id,
            amount=f"{created_tx.amount:.2f}",
            transaction_type=created_tx.transaction_type,
            status=created_tx.status,
            transaction_date=created_tx.transaction_date,
            due_date=created_tx.due_date,
            description=created_tx.description,
            source_account=SourceAccountSummary(
                id=source_account.id,
                name=source_account.name,
                new_balance=f"{source_account.balance:.2f}",
            ),
            category_id=created_tx.category_id,
            installment_id=created_tx.installment_id,
            installment_number=created_tx.installment_number,
            total_installments=created_tx.total_installments,
            total_amount=f"{total_amount:.2f}" if total_amount is not None else None,
            created_at=created_tx.created_at,
        )
        return response.model_dump(mode="json")


class GetStatementUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
        category_repo: ICategoryRepository,
    ) -> None:
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    async def execute(self, payload: GetStatementInput) -> dict[str, Any]:
        s_date = datetime.fromisoformat(payload.start_date)
        if s_date.tzinfo is None:
            s_date = s_date.replace(tzinfo=UTC)
        e_date = datetime.fromisoformat(payload.end_date)
        if e_date.tzinfo is None:
            e_date = e_date.replace(tzinfo=UTC)

        account = await self.account_repo.get_by_id(
            payload.account_id, user_id=payload.user_id, only_active=False
        )
        if not account:
            raise AccountNotFoundError(str(payload.account_id))

        transactions = await self.transaction_repo.list_by_account(
            account_id=payload.account_id,
            user_id=payload.user_id,
            start_date=s_date,
            end_date=e_date,
            date_type=payload.date_type,
            search=payload.search,
            limit=payload.limit,
        )
        if not payload.include_pending:
            transactions = [
                tx for tx in transactions if tx.status == TransactionStatus.CLEARED
            ]

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
                cat = await self.category_repo.get_by_id(
                    tx.category_id, user_id=payload.user_id, only_active=False
                )
                if cat:
                    category_name = cat.name

            items.append(
                StatementItem(
                    id=tx.id,
                    transaction_date=tx.transaction_date,
                    due_date=tx.due_date or tx.transaction_date,
                    description=tx.description,
                    amount=f"{tx.amount:.2f}",
                    transaction_type=tx.transaction_type,
                    status=tx.status,
                    category=category_name,
                    installment_id=tx.installment_id,
                    installment_number=tx.installment_number,
                    total_installments=tx.total_installments,
                    total_amount=None,
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
                date_type=payload.date_type,
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


class GetInstallmentPlanUseCase:
    def __init__(self, transaction_repo: ITransactionRepository) -> None:
        self.transaction_repo = transaction_repo

    async def execute(self, payload: GetInstallmentPlanInput) -> dict[str, Any]:
        transactions = await self.transaction_repo.list_by_installment_id(
            payload.installment_id, user_id=payload.user_id
        )
        if not transactions:
            raise InstallmentPlanNotFoundError(str(payload.installment_id))

        first_tx = transactions[0]
        total_amount = sum((t.amount for t in transactions), Decimal("0.00"))
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


class DeleteTransactionUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    async def execute(self, payload: DeleteTransactionInput) -> dict[str, Any]:
        tx = await self.transaction_repo.get_by_id(
            payload.transaction_id, user_id=payload.user_id
        )
        if not tx:
            raise TransactionNotFoundError(str(payload.transaction_id))

        transactions_to_delete = []
        if payload.delete_all_installments and tx.installment_id is not None:
            transactions_to_delete = await self.transaction_repo.list_by_installment_id(
                tx.installment_id, user_id=payload.user_id
            )
        else:
            transactions_to_delete = [tx]

        reverted_total = Decimal("0.00")
        for item in transactions_to_delete:
            if item.status == TransactionStatus.CLEARED:
                source_account = await self.account_repo.get_by_id(
                    item.source_account_id, user_id=payload.user_id, only_active=False
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
                            dest = await self.account_repo.get_by_id(
                                item.destination_account_id,
                                user_id=payload.user_id,
                                only_active=False,
                            )
                            if dest:
                                dest.balance -= item.amount
                                await self.account_repo.update(dest)
                    await self.account_repo.update(source_account)

            await self.transaction_repo.delete(item.id, user_id=payload.user_id)

        count = len(transactions_to_delete)
        return DeleteTransactionResponse(
            transaction_id=payload.transaction_id,
            deleted_count=count,
            reverted_amount=f"{reverted_total:.2f}",
            message=f"Successfully deleted {count} transaction(s) and reverted R$ {reverted_total:.2f}.",
        ).model_dump(mode="json")


class GetFinancialSummaryUseCase:
    def __init__(self, account_repo: IAccountRepository) -> None:
        self.account_repo = account_repo

    async def execute(self, payload: GetFinancialSummaryInput) -> dict[str, Any]:
        if payload.reference_date:
            ref_date = payload.reference_date
        elif payload.year and payload.month:
            ref_date = f"{payload.year:04d}-{payload.month:02d}-01"
        elif payload.year:
            ref_date = f"{payload.year:04d}-01-01"
        elif payload.month:
            now = datetime.now(UTC).date()
            ref_date = f"{now.year:04d}-{payload.month:02d}-01"
        else:
            ref_date = datetime.now(UTC).date().isoformat()

        accounts = await self.account_repo.list_all(
            user_id=payload.user_id, only_active=True, limit=1000
        )

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
