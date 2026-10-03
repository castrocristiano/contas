from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from contas.domain.enums import (
    AccountType,
    CategoryType,
    TransactionStatus,
    TransactionType,
)


@dataclass
class User:
    name: str
    email: str
    username: str
    id: UUID = field(default_factory=uuid4)
    password_hash: str | None = None
    auth_provider: str = "local"
    google_id: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    is_approved: bool = False
    role: str = "user"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


_DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


@dataclass
class Account:
    name: str
    account_type: AccountType
    user_id: UUID = _DEFAULT_USER_ID
    id: UUID = field(default_factory=uuid4)
    balance: Decimal = Decimal("0.00")
    currency: str = "BRL"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def deposit(self, amount: Decimal) -> None:
        self.balance += amount

    def withdraw(self, amount: Decimal) -> None:
        self.balance -= amount


@dataclass
class Category:
    name: str
    category_type: CategoryType
    user_id: UUID = _DEFAULT_USER_ID
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Transaction:
    amount: Decimal
    transaction_type: TransactionType
    source_account_id: UUID
    user_id: UUID = _DEFAULT_USER_ID
    id: UUID = field(default_factory=uuid4)
    destination_account_id: UUID | None = None
    category_id: UUID | None = None
    status: TransactionStatus = TransactionStatus.CLEARED
    transaction_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    due_date: datetime | None = None
    description: str = ""
    installment_id: UUID | None = None
    installment_number: int | None = None
    total_installments: int | None = None
    total_amount: Decimal | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Budget:
    category_id: UUID
    month: int
    year: int
    amount: Decimal
    user_id: UUID = _DEFAULT_USER_ID
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
