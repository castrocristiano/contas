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
class Account:
    name: str
    account_type: AccountType
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
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Transaction:
    amount: Decimal
    transaction_type: TransactionType
    source_account_id: UUID
    id: UUID = field(default_factory=uuid4)
    destination_account_id: UUID | None = None
    category_id: UUID | None = None
    status: TransactionStatus = TransactionStatus.CLEARED
    transaction_date: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
