import pytest

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.models.transaction import TransactionStatus, TransactionType


def test_account_type_values():
    assert AccountType("checking") == AccountType.CHECKING
    assert AccountType("savings") == AccountType.SAVINGS
    assert AccountType("investment") == AccountType.INVESTMENT
    assert AccountType("cash") == AccountType.CASH

    with pytest.raises(ValueError):
        AccountType("invalid")


def test_category_type_values():
    assert CategoryType("income") == CategoryType.INCOME
    assert CategoryType("expense") == CategoryType.EXPENSE

    with pytest.raises(ValueError):
        CategoryType("invalid")


def test_transaction_type_values():
    assert TransactionType("income") == TransactionType.INCOME
    assert TransactionType("expense") == TransactionType.EXPENSE
    assert TransactionType("transfer") == TransactionType.TRANSFER

    with pytest.raises(ValueError):
        TransactionType("invalid")


def test_transaction_status_values():
    assert TransactionStatus("cleared") == TransactionStatus.CLEARED
    assert TransactionStatus("pending") == TransactionStatus.PENDING

    with pytest.raises(ValueError):
        TransactionStatus("invalid")
