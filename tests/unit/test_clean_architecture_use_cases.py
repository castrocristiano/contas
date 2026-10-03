from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from contas.application.ports.repositories import (
    IAccountRepository,
    ICategoryRepository,
    ITransactionRepository,
)
from contas.application.use_cases.accounts import (
    CreateAccountUseCase,
    ListAccountsUseCase,
    UpdateAccountUseCase,
)
from contas.application.use_cases.transactions import (
    RecordTransactionUseCase,
)
from contas.domain.entities import Account, Category, Transaction
from contas.domain.enums import (
    AccountType,
    TransactionType,
)
from contas.domain.errors import (
    AccountNotFoundError,
)
from contas.schemas.account import (
    CreateAccountInput,
    ListAccountsInput,
    UpdateAccountInput,
)
from contas.schemas.transaction import (
    RecordTransactionInput,
)


class InMemoryAccountRepository(IAccountRepository):
    def __init__(self):
        self.accounts: dict[UUID, Account] = {}

    async def get_by_id(
        self, account_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> Account | None:
        acc = self.accounts.get(account_id)
        if acc and user_id and acc.user_id != user_id:
            return None
        if acc and only_active and not acc.is_active:
            return None
        return acc

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        account_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Account]:
        res = list(self.accounts.values())
        if user_id:
            res = [a for a in res if a.user_id == user_id]
        if only_active:
            res = [a for a in res if a.is_active]
        if account_type:
            res = [a for a in res if a.account_type == account_type]
        return res[offset : offset + limit]

    async def create(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

    async def update(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

    async def delete(self, account_id: UUID, user_id: UUID | None = None) -> bool:
        if account_id in self.accounts:
            if user_id and self.accounts[account_id].user_id != user_id:
                return False
            del self.accounts[account_id]
            return True
        return False

    async def bulk_delete(
        self,
        account_ids: list[UUID],
        cascade: bool = False,
        user_id: UUID | None = None,
    ) -> int:
        count = 0
        for aid in account_ids:
            if aid in self.accounts:
                if user_id and self.accounts[aid].user_id != user_id:
                    continue
                del self.accounts[aid]
                count += 1
        return count


class InMemoryCategoryRepository(ICategoryRepository):
    def __init__(self):
        self.categories: dict[UUID, Category] = {}

    async def get_by_id(
        self, category_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> Category | None:
        cat = self.categories.get(category_id)
        if cat and user_id and cat.user_id != user_id:
            return None
        if cat and only_active and not cat.is_active:
            return None
        return cat

    async def get_by_name(
        self, name: str, user_id: UUID | None = None
    ) -> Category | None:
        for c in self.categories.values():
            if c.name == name and (user_id is None or c.user_id == user_id):
                return c
        return None

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        category_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Category]:
        res = list(self.categories.values())
        if user_id:
            res = [c for c in res if c.user_id == user_id]
        if only_active:
            res = [c for c in res if c.is_active]
        if category_type:
            res = [c for c in res if c.category_type == category_type]
        return res[offset : offset + limit]

    async def create(self, category: Category) -> Category:
        self.categories[category.id] = category
        return category


class InMemoryTransactionRepository(ITransactionRepository):
    def __init__(self):
        self.transactions: dict[UUID, Transaction] = {}

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self.transactions.get(transaction_id)

    async def create(self, transaction: Transaction) -> Transaction:
        self.transactions[transaction.id] = transaction
        return transaction

    async def create_many(self, transactions: list[Transaction]) -> list[Transaction]:
        for t in transactions:
            self.transactions[t.id] = t
        return transactions

    async def delete(self, transaction_id: UUID) -> bool:
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
            return True
        return False

    async def bulk_delete(self, transaction_ids: list[UUID]) -> int:
        count = 0
        for tid in transaction_ids:
            if tid in self.transactions:
                del self.transactions[tid]
                count += 1
        return count

    async def list_by_account(
        self,
        account_id: UUID,
        user_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_type: str = "transaction_date",
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        res = [
            t
            for t in self.transactions.values()
            if t.source_account_id == account_id
            and (user_id is None or t.user_id == user_id)
        ]
        if search:
            res = [t for t in res if search.lower() in t.description.lower()]
        if start_date or end_date:
            filtered = []
            for t in res:
                d = (
                    (t.due_date or t.transaction_date)
                    if date_type == "due_date"
                    else t.transaction_date
                )
                if start_date and d < start_date:
                    continue
                if end_date and d > end_date:
                    continue
                filtered.append(t)
            res = filtered
        return res[offset : offset + limit]

    async def list_by_installment_id(self, installment_id: UUID) -> list[Transaction]:
        return [
            t for t in self.transactions.values() if t.installment_id == installment_id
        ]

    async def delete_by_installment_id(self, installment_id: UUID) -> list[Transaction]:
        deleted = []
        for tid, t in list(self.transactions.items()):
            if t.installment_id == installment_id:
                deleted.append(t)
                del self.transactions[tid]
        return deleted

    async def count_by_account(
        self, account_id: UUID, user_id: UUID | None = None
    ) -> int:
        return len(
            [
                t
                for t in self.transactions.values()
                if (
                    t.source_account_id == account_id
                    or t.destination_account_id == account_id
                )
                and (user_id is None or t.user_id == user_id)
            ]
        )

    async def get_summary_by_account(
        self,
        account_id: UUID,
        user_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_type: str = "transaction_date",
    ) -> dict[str, Decimal]:
        return {
            "income": Decimal("0.00"),
            "expense": Decimal("0.00"),
            "net": Decimal("0.00"),
        }


@pytest.mark.anyio
async def test_create_and_list_account_use_cases_pure_in_memory():
    repo = InMemoryAccountRepository()
    create_uc = CreateAccountUseCase(repo)
    list_uc = ListAccountsUseCase(repo)

    created = await create_uc.execute(
        CreateAccountInput(
            name="Conta Teste",
            account_type=AccountType.CHECKING,
            initial_balance="250.00",
        )
    )
    assert created["name"] == "Conta Teste"
    assert created["balance"] == "250.00"

    listed = await list_uc.execute(ListAccountsInput())
    assert listed["count"] == 1
    assert listed["total_balance"] == "250.00"


@pytest.mark.anyio
async def test_record_transaction_missing_account_raises_domain_error():
    account_repo = InMemoryAccountRepository()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()
    uc = RecordTransactionUseCase(account_repo, tx_repo, cat_repo)

    missing_id = uuid4()
    with pytest.raises(AccountNotFoundError):
        await uc.execute(
            RecordTransactionInput(
                amount="50.00",
                transaction_type=TransactionType.EXPENSE,
                source_account_id=missing_id,
            )
        )


@pytest.mark.anyio
async def test_record_transaction_expense_updates_balance_in_memory():
    account_repo = InMemoryAccountRepository()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()

    acc = Account(
        name="Nubank",
        account_type=AccountType.CHECKING,
        balance=Decimal("500.00"),
    )
    await account_repo.create(acc)

    uc = RecordTransactionUseCase(account_repo, tx_repo, cat_repo)
    res = await uc.execute(
        RecordTransactionInput(
            amount="120.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc.id,
            description="Restaurante",
        )
    )

    assert res["source_account"]["new_balance"] == "380.00"
    updated_acc = await account_repo.get_by_id(acc.id)
    assert updated_acc.balance == Decimal("380.00")


@pytest.mark.anyio
async def test_get_financial_summary_use_case():
    from contas.application.use_cases.transactions import GetFinancialSummaryUseCase
    from contas.schemas.transaction import GetFinancialSummaryInput

    account_repo = InMemoryAccountRepository()
    acc = Account(
        name="Conta Corrente",
        account_type=AccountType.CHECKING,
        balance=Decimal("1500.50"),
    )
    await account_repo.create(acc)

    uc = GetFinancialSummaryUseCase(account_repo)

    # With month and year
    res = await uc.execute(GetFinancialSummaryInput(month=10, year=2026))
    assert res["reference_date"] == "2026-10-01"
    assert res["total_assets"] == "1500.50"
    assert len(res["accounts"]) == 1

    # With reference_date
    res2 = await uc.execute(GetFinancialSummaryInput(reference_date="2026-05-15"))
    assert res2["reference_date"] == "2026-05-15"


@pytest.mark.anyio
async def test_create_credit_card_account():
    account_repo = InMemoryAccountRepository()
    uc = CreateAccountUseCase(account_repo)

    res = await uc.execute(
        CreateAccountInput(
            name="Cartão Nubank",
            account_type=AccountType.CREDIT_CARD,
            initial_balance="0.00",
        )
    )
    assert res["account_type"] == "credit_card"
    created = await account_repo.get_by_id(UUID(res["id"]))
    assert created is not None
    assert created.account_type == AccountType.CREDIT_CARD


@pytest.mark.anyio
async def test_record_transaction_with_due_date():
    account_repo = InMemoryAccountRepository()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()

    acc = Account(
        name="Cartão",
        account_type=AccountType.CREDIT_CARD,
        balance=Decimal("0.00"),
    )
    await account_repo.create(acc)

    uc = RecordTransactionUseCase(account_repo, tx_repo, cat_repo)

    # 1. With explicit due_date
    res1 = await uc.execute(
        RecordTransactionInput(
            amount="250.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc.id,
            description="Compra Online",
            transaction_date="2026-10-01",
            due_date="2026-10-20",
        )
    )
    tx1 = await tx_repo.get_by_id(UUID(res1["id"]))
    assert tx1.due_date == datetime(2026, 10, 20, tzinfo=UTC)
    assert "2026-10-20" in res1["due_date"]

    # 2. Without due_date (defaults to transaction_date)
    res2 = await uc.execute(
        RecordTransactionInput(
            amount="50.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc.id,
            description="Lanche",
            transaction_date="2026-10-02",
        )
    )
    tx2 = await tx_repo.get_by_id(UUID(res2["id"]))
    assert tx2.due_date == datetime(2026, 10, 2, tzinfo=UTC)
    assert "2026-10-02" in res2["due_date"]


@pytest.mark.anyio
async def test_record_installment_transaction_with_due_date():
    account_repo = InMemoryAccountRepository()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()

    acc = Account(
        name="Cartão",
        account_type=AccountType.CREDIT_CARD,
        balance=Decimal("0.00"),
    )
    await account_repo.create(acc)

    uc = RecordTransactionUseCase(account_repo, tx_repo, cat_repo)

    res = await uc.execute(
        RecordTransactionInput(
            amount="100.00",
            total_amount="300.00",
            total_installments=3,
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc.id,
            description="Eletrônico",
            transaction_date="2026-10-05",
            due_date="2026-10-25",
        )
    )
    installments = await tx_repo.list_by_installment_id(UUID(res["installment_id"]))
    assert len(installments) == 3
    # Sorted by installment_number
    installments.sort(key=lambda x: x.installment_number)

    assert installments[0].transaction_date == datetime(2026, 10, 5, tzinfo=UTC)
    assert installments[0].due_date == datetime(2026, 10, 25, tzinfo=UTC)

    assert installments[1].transaction_date == datetime(2026, 11, 5, tzinfo=UTC)
    assert installments[1].due_date == datetime(2026, 11, 25, tzinfo=UTC)

    assert installments[2].transaction_date == datetime(2026, 12, 5, tzinfo=UTC)
    assert installments[2].due_date == datetime(2026, 12, 25, tzinfo=UTC)


@pytest.mark.anyio
async def test_get_statement_filter_by_date_type():
    from contas.application.use_cases.transactions import GetStatementUseCase
    from contas.schemas.transaction import GetStatementInput

    account_repo = InMemoryAccountRepository()
    tx_repo = InMemoryTransactionRepository()
    cat_repo = InMemoryCategoryRepository()

    acc = Account(
        name="Cartão",
        account_type=AccountType.CREDIT_CARD,
        balance=Decimal("0.00"),
    )
    await account_repo.create(acc)

    # tx1: transaction_date in Sept, due_date in Oct
    tx1 = Transaction(
        amount=Decimal("100.00"),
        transaction_type=TransactionType.EXPENSE,
        source_account_id=acc.id,
        description="Compra Setembro",
        transaction_date=datetime(2026, 9, 28, tzinfo=UTC),
        due_date=datetime(2026, 10, 10, tzinfo=UTC),
    )
    await tx_repo.create(tx1)

    # tx2: transaction_date in Oct, due_date in Nov
    tx2 = Transaction(
        amount=Decimal("200.00"),
        transaction_type=TransactionType.EXPENSE,
        source_account_id=acc.id,
        description="Compra Outubro",
        transaction_date=datetime(2026, 10, 5, tzinfo=UTC),
        due_date=datetime(2026, 11, 10, tzinfo=UTC),
    )
    await tx_repo.create(tx2)

    uc = GetStatementUseCase(account_repo, tx_repo, cat_repo)

    # Query with date_type="transaction_date" for October (2026-10-01 to 2026-10-31)
    res_tx_date = await uc.execute(
        GetStatementInput(
            account_id=acc.id,
            start_date="2026-10-01",
            end_date="2026-10-31",
            date_type="transaction_date",
        )
    )
    assert len(res_tx_date["transactions"]) == 1
    assert res_tx_date["transactions"][0]["description"] == "Compra Outubro"

    # Query with date_type="due_date" for October (2026-10-01 to 2026-10-31)
    res_due_date = await uc.execute(
        GetStatementInput(
            account_id=acc.id,
            start_date="2026-10-01",
            end_date="2026-10-31",
            date_type="due_date",
        )
    )
    assert len(res_due_date["transactions"]) == 1
    assert res_due_date["transactions"][0]["description"] == "Compra Setembro"
    assert "2026-10-10" in res_due_date["transactions"][0]["due_date"]


@pytest.mark.anyio
async def test_update_account_use_case_success():
    repo = InMemoryAccountRepository()
    acc = Account(
        name="Nubank Antigo",
        account_type=AccountType.CHECKING,
        balance=Decimal("100.00"),
    )
    await repo.create(acc)

    uc = UpdateAccountUseCase(repo)
    updated = await uc.execute(
        UpdateAccountInput(
            account_id=acc.id,
            name="Nubank Principal",
        )
    )

    assert updated["id"] == str(acc.id)
    assert updated["name"] == "Nubank Principal"
    persisted = await repo.get_by_id(acc.id)
    assert persisted is not None
    assert persisted.name == "Nubank Principal"


@pytest.mark.anyio
async def test_update_account_use_case_not_found():
    repo = InMemoryAccountRepository()
    uc = UpdateAccountUseCase(repo)

    with pytest.raises(AccountNotFoundError):
        await uc.execute(
            UpdateAccountInput(
                account_id=uuid4(),
                name="Inexistente",
            )
        )
