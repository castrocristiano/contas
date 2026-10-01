from enum import StrEnum


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CASH = "cash"
    CREDIT_CARD = "credit_card"


class CategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    CLEARED = "cleared"
    PENDING = "pending"
