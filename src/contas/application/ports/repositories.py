from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from contas.domain.entities import Account, Budget, Category, Transaction, User


class IUserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def get_by_google_id(self, google_id: str) -> User | None: ...

    async def count(self) -> int: ...

    async def get_default_user(self) -> User | None: ...

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]: ...

    async def create(self, user: User) -> User: ...

    async def update(self, user: User) -> User: ...


class IAccountRepository(Protocol):
    async def get_by_id(
        self, account_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> Account | None: ...

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        account_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Account]: ...

    async def create(self, account: Account) -> Account: ...

    async def update(self, account: Account) -> Account: ...

    async def delete(self, account_id: UUID, user_id: UUID | None = None) -> bool: ...

    async def bulk_delete(
        self,
        account_ids: list[UUID],
        user_id: UUID | None = None,
        cascade: bool = False,
    ) -> int: ...


class ICategoryRepository(Protocol):
    async def get_by_id(
        self, category_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> Category | None: ...

    async def get_by_name(
        self, name: str, user_id: UUID | None = None
    ) -> Category | None: ...

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        category_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Category]: ...

    async def create(self, category: Category) -> Category: ...


class ITransactionRepository(Protocol):
    async def get_by_id(
        self, transaction_id: UUID, user_id: UUID | None = None
    ) -> Transaction | None: ...

    async def create(self, transaction: Transaction) -> Transaction: ...

    async def create_many(
        self, transactions: list[Transaction]
    ) -> list[Transaction]: ...

    async def delete(
        self, transaction_id: UUID, user_id: UUID | None = None
    ) -> bool: ...

    async def bulk_delete(
        self, transaction_ids: list[UUID], user_id: UUID | None = None
    ) -> int: ...

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
    ) -> list[Transaction]: ...

    async def list_by_installment_id(
        self, installment_id: UUID, user_id: UUID | None = None
    ) -> list[Transaction]: ...

    async def delete_by_installment_id(
        self, installment_id: UUID, user_id: UUID | None = None
    ) -> list[Transaction]: ...

    async def count_by_account(
        self, account_id: UUID, user_id: UUID | None = None
    ) -> int: ...

    async def get_summary_by_account(
        self,
        account_id: UUID,
        user_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_type: str = "transaction_date",
    ) -> dict[str, Decimal]: ...


class IBudgetRepository(Protocol):
    async def get(
        self, category_id: UUID, month: int, year: int, user_id: UUID | None = None
    ) -> Budget | None: ...

    async def set_budget(self, budget: Budget) -> Budget: ...

    async def get_spent_for_category(
        self, category_id: UUID, month: int, year: int, user_id: UUID | None = None
    ) -> Decimal: ...
