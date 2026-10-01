from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from contas.domain.entities import Account, Budget, Category, Transaction


class IAccountRepository(Protocol):
    async def get_by_id(
        self, account_id: UUID, only_active: bool = True
    ) -> Account | None: ...

    async def list_all(
        self,
        only_active: bool = True,
        account_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Account]: ...

    async def create(self, account: Account) -> Account: ...

    async def update(self, account: Account) -> Account: ...

    async def delete(self, account_id: UUID) -> bool: ...

    async def bulk_delete(
        self, account_ids: list[UUID], cascade: bool = False
    ) -> int: ...


class ICategoryRepository(Protocol):
    async def get_by_id(
        self, category_id: UUID, only_active: bool = True
    ) -> Category | None: ...

    async def get_by_name(self, name: str) -> Category | None: ...

    async def list_all(
        self,
        only_active: bool = True,
        category_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Category]: ...

    async def create(self, category: Category) -> Category: ...


class ITransactionRepository(Protocol):
    async def get_by_id(self, transaction_id: UUID) -> Transaction | None: ...

    async def create(self, transaction: Transaction) -> Transaction: ...

    async def create_many(
        self, transactions: list[Transaction]
    ) -> list[Transaction]: ...

    async def delete(self, transaction_id: UUID) -> bool: ...

    async def bulk_delete(self, transaction_ids: list[UUID]) -> int: ...

    async def list_by_account(
        self,
        account_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]: ...

    async def list_by_installment_id(
        self, installment_id: UUID
    ) -> list[Transaction]: ...

    async def delete_by_installment_id(
        self, installment_id: UUID
    ) -> list[Transaction]: ...

    async def count_by_account(self, account_id: UUID) -> int: ...

    async def get_summary_by_account(
        self,
        account_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Decimal]: ...


class IBudgetRepository(Protocol):
    async def get(self, category_id: UUID, month: int, year: int) -> Budget | None: ...

    async def set_budget(self, budget: Budget) -> Budget: ...

    async def get_spent_for_category(
        self, category_id: UUID, month: int, year: int
    ) -> Decimal: ...
