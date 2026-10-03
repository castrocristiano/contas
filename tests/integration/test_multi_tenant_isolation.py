from decimal import Decimal
from uuid import uuid4

import pytest

from contas.application.ports.repositories import (
    IAccountRepository,
    ICategoryRepository,
    ITransactionRepository,
)
from contas.application.use_cases.accounts import (
    CreateAccountUseCase,
    ListAccountsUseCase,
)
from contas.application.use_cases.transactions import (
    GetStatementUseCase,
    RecordTransactionUseCase,
)
from contas.domain.enums import AccountType, TransactionType
from contas.schemas.account import CreateAccountInput, ListAccountsInput
from contas.schemas.transaction import GetStatementInput, RecordTransactionInput


class InMemoryMultiTenantAccountRepo(IAccountRepository):
    def __init__(self):
        self.accounts: dict = {}

    async def get_by_id(self, account_id, user_id=None, only_active=True):
        acc = self.accounts.get(account_id)
        if not acc:
            return None
        if user_id and acc.user_id != user_id:
            return None
        if only_active and not acc.is_active:
            return None
        return acc

    async def list_all(
        self, user_id=None, only_active=True, account_type=None, limit=50, offset=0
    ):
        res = list(self.accounts.values())
        if user_id:
            res = [a for a in res if a.user_id == user_id]
        if only_active:
            res = [a for a in res if a.is_active]
        return res[offset : offset + limit]

    async def create(self, account):
        self.accounts[account.id] = account
        return account

    async def update(self, account):
        self.accounts[account.id] = account
        return account

    async def delete(self, account_id, user_id=None):
        if account_id in self.accounts:
            if user_id and self.accounts[account_id].user_id != user_id:
                return False
            del self.accounts[account_id]
            return True
        return False

    async def bulk_delete(self, account_ids, user_id=None, cascade=False):
        c = 0
        for aid in account_ids:
            if aid in self.accounts:
                if user_id and self.accounts[aid].user_id != user_id:
                    continue
                del self.accounts[aid]
                c += 1
        return c


class InMemoryMultiTenantTxRepo(ITransactionRepository):
    def __init__(self):
        self.transactions: dict = {}

    async def get_by_id(self, transaction_id, user_id=None):
        tx = self.transactions.get(transaction_id)
        if tx and user_id and tx.user_id != user_id:
            return None
        return tx

    async def create(self, transaction):
        self.transactions[transaction.id] = transaction
        return transaction

    async def create_many(self, transactions):
        for tx in transactions:
            self.transactions[tx.id] = tx
        return transactions

    async def delete(self, transaction_id, user_id=None):
        if transaction_id in self.transactions:
            if user_id and self.transactions[transaction_id].user_id != user_id:
                return False
            del self.transactions[transaction_id]
            return True
        return False

    async def bulk_delete(self, transaction_ids, user_id=None):
        c = 0
        for tid in transaction_ids:
            if tid in self.transactions:
                if user_id and self.transactions[tid].user_id != user_id:
                    continue
                del self.transactions[tid]
                c += 1
        return c

    async def list_by_account(
        self,
        account_id,
        user_id=None,
        start_date=None,
        end_date=None,
        date_type="transaction_date",
        search=None,
        limit=50,
        offset=0,
    ):
        res = [
            t for t in self.transactions.values() if t.source_account_id == account_id
        ]
        if user_id:
            res = [t for t in res if t.user_id == user_id]
        return res[offset : offset + limit]

    async def list_by_installment_id(self, installment_id, user_id=None):
        res = [
            t for t in self.transactions.values() if t.installment_id == installment_id
        ]
        if user_id:
            res = [t for t in res if t.user_id == user_id]
        return res

    async def delete_by_installment_id(self, installment_id, user_id=None):
        del_list = []
        for tid, t in list(self.transactions.items()):
            if t.installment_id == installment_id:
                if user_id and t.user_id != user_id:
                    continue
                del_list.append(t)
                del self.transactions[tid]
        return del_list

    async def count_by_account(self, account_id, user_id=None):
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
        account_id,
        user_id=None,
        start_date=None,
        end_date=None,
        date_type="transaction_date",
    ):
        return {
            "income": Decimal("0.00"),
            "expense": Decimal("0.00"),
            "net": Decimal("0.00"),
        }


class InMemoryMultiTenantCatRepo(ICategoryRepository):
    def __init__(self):
        self.categories: dict = {}

    async def get_by_id(self, category_id, user_id=None, only_active=True):
        c = self.categories.get(category_id)
        if c and user_id and c.user_id != user_id:
            return None
        return c

    async def get_by_name(self, name, user_id=None):
        for c in self.categories.values():
            if c.name == name and (user_id is None or c.user_id == user_id):
                return c
        return None

    async def list_all(
        self, user_id=None, only_active=True, category_type=None, limit=50, offset=0
    ):
        res = list(self.categories.values())
        if user_id:
            res = [c for c in res if c.user_id == user_id]
        return res[offset : offset + limit]

    async def create(self, category):
        self.categories[category.id] = category
        return category


@pytest.mark.anyio
async def test_multi_tenant_isolation_user_a_and_user_b():
    user_a_id = uuid4()
    user_b_id = uuid4()

    acc_repo = InMemoryMultiTenantAccountRepo()
    tx_repo = InMemoryMultiTenantTxRepo()
    cat_repo = InMemoryMultiTenantCatRepo()

    create_acc_uc = CreateAccountUseCase(acc_repo)
    list_acc_uc = ListAccountsUseCase(acc_repo)
    rec_tx_uc = RecordTransactionUseCase(acc_repo, tx_repo, cat_repo)
    stmt_uc = GetStatementUseCase(acc_repo, tx_repo, cat_repo)

    # 1. User A cria conta e lança despesa
    acc_a = await create_acc_uc.execute(
        CreateAccountInput(
            name="Conta Privada de A",
            account_type=AccountType.CHECKING,
            initial_balance="1000.00",
            user_id=user_a_id,
        )
    )
    acc_a_id = acc_a["id"]

    await rec_tx_uc.execute(
        RecordTransactionInput(
            amount="150.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_a_id,
            description="Despesa Pessoal de A",
            user_id=user_a_id,
        )
    )

    # 2. User B lista suas contas -> Não deve ver nada
    list_b = await list_acc_uc.execute(ListAccountsInput(user_id=user_b_id))
    assert list_b["count"] == 0
    assert len(list_b["accounts"]) == 0

    # 3. User A lista suas contas -> Vê sua conta com saldo atualizado
    list_a = await list_acc_uc.execute(ListAccountsInput(user_id=user_a_id))
    assert list_a["count"] == 1
    assert list_a["accounts"][0]["name"] == "Conta Privada de A"

    # 4. User B tenta puxar extrato da conta de A -> AccountNotFoundError
    from contas.domain.errors import AccountNotFoundError

    with pytest.raises(AccountNotFoundError):
        await stmt_uc.execute(
            GetStatementInput(
                account_id=acc_a_id,
                start_date="2026-01-01",
                end_date="2026-12-31",
                user_id=user_b_id,
            )
        )
