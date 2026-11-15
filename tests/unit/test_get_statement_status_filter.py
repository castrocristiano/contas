import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from contas.application.use_cases.transactions import GetStatementUseCase
from contas.domain.entities import Account, Transaction
from contas.domain.enums import AccountType, TransactionStatus, TransactionType
from contas.schemas.transaction import GetStatementInput, StatementStatusFilter


@pytest.fixture
def mock_repos():
    account_repo = AsyncMock()
    transaction_repo = AsyncMock()
    category_repo = AsyncMock()
    return account_repo, transaction_repo, category_repo


@pytest.fixture
def sample_account():
    return Account(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Account",
        account_type=AccountType.CHECKING,
        balance=Decimal("1500.00"),
        is_active=True,
    )


@pytest.fixture
def sample_transactions(sample_account):
    now = datetime.now(UTC)
    tx_cleared_expense = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("100.00"),
        transaction_type=TransactionType.EXPENSE,
        status=TransactionStatus.CLEARED,
        transaction_date=now,
        description="Mercado",
        source_account_id=sample_account.id,
    )
    tx_pending_expense = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("50.00"),
        transaction_type=TransactionType.EXPENSE,
        status=TransactionStatus.PENDING,
        transaction_date=now,
        description="Conta de Luz",
        source_account_id=sample_account.id,
    )
    tx_cleared_income = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("500.00"),
        transaction_type=TransactionType.INCOME,
        status=TransactionStatus.CLEARED,
        transaction_date=now,
        description="Salario",
        source_account_id=sample_account.id,
    )
    tx_pending_income = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("200.00"),
        transaction_type=TransactionType.INCOME,
        status=TransactionStatus.PENDING,
        transaction_date=now,
        description="Freela",
        source_account_id=sample_account.id,
    )
    return [
        tx_cleared_expense,
        tx_pending_expense,
        tx_cleared_income,
        tx_pending_income,
    ]


@pytest.mark.anyio
async def test_get_statement_filter_pending_only(
    mock_repos, sample_account, sample_transactions
):
    account_repo, transaction_repo, category_repo = mock_repos
    account_repo.get_by_id.return_value = sample_account
    # Mocking repo to return all matching date range
    transaction_repo.list_by_account.return_value = sample_transactions

    use_case = GetStatementUseCase(account_repo, transaction_repo, category_repo)

    payload = GetStatementInput(
        account_id=sample_account.id,
        start_date="2026-11-01",
        end_date="2026-11-30",
        status_filter=StatementStatusFilter.PENDING,
    )

    result = await use_case.execute(payload)

    # Verify only pending transactions returned
    returned_txs = result["transactions"]
    assert len(returned_txs) == 2
    for t in returned_txs:
        assert t["status"] == "pending"

    # Summary: pending income (200), pending expense (50), net (150)
    summary = result["summary"]
    assert summary["total_income"] == "200.00"
    assert summary["total_expense"] == "50.00"
    assert summary["net"] == "150.00"
    assert summary["count"] == 2


@pytest.mark.anyio
async def test_get_statement_filter_cleared_only(
    mock_repos, sample_account, sample_transactions
):
    account_repo, transaction_repo, category_repo = mock_repos
    account_repo.get_by_id.return_value = sample_account
    transaction_repo.list_by_account.return_value = sample_transactions

    use_case = GetStatementUseCase(account_repo, transaction_repo, category_repo)

    payload = GetStatementInput(
        account_id=sample_account.id,
        start_date="2026-11-01",
        end_date="2026-11-30",
        status_filter=StatementStatusFilter.CLEARED,
    )

    result = await use_case.execute(payload)

    returned_txs = result["transactions"]
    assert len(returned_txs) == 2
    for t in returned_txs:
        assert t["status"] == "cleared"

    # Summary: cleared income (500), cleared expense (100), net (400)
    summary = result["summary"]
    assert summary["total_income"] == "500.00"
    assert summary["total_expense"] == "100.00"
    assert summary["net"] == "400.00"
    assert summary["count"] == 2


@pytest.mark.anyio
async def test_get_statement_filter_all_includes_pending(
    mock_repos, sample_account, sample_transactions
):
    account_repo, transaction_repo, category_repo = mock_repos
    account_repo.get_by_id.return_value = sample_account
    transaction_repo.list_by_account.return_value = sample_transactions

    use_case = GetStatementUseCase(account_repo, transaction_repo, category_repo)

    payload = GetStatementInput(
        account_id=sample_account.id,
        start_date="2026-11-01",
        end_date="2026-11-30",
        include_pending=True,
        status_filter=StatementStatusFilter.ALL,
    )

    result = await use_case.execute(payload)

    returned_txs = result["transactions"]
    assert len(returned_txs) == 4
    summary = result["summary"]
    assert summary["total_income"] == "700.00"
    assert summary["total_expense"] == "150.00"
    assert summary["net"] == "550.00"
    assert summary["count"] == 4
