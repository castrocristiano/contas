import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from contas.application.use_cases.transactions import GetDashboardProjectionsUseCase
from contas.domain.entities import Account, Transaction
from contas.domain.enums import AccountType, TransactionStatus, TransactionType
from contas.schemas.account import GetDashboardProjectionsInput


@pytest.fixture
def mock_repos():
    account_repo = AsyncMock()
    transaction_repo = AsyncMock()
    return account_repo, transaction_repo


@pytest.fixture
def sample_account():
    return Account(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Conta Principal",
        account_type=AccountType.CHECKING,
        balance=Decimal("1000.00"),
        is_active=True,
    )


@pytest.mark.anyio
async def test_dashboard_projections_calculation(mock_repos, sample_account):
    account_repo, transaction_repo = mock_repos
    account_repo.list_all.return_value = [sample_account]

    now = datetime.now(UTC)
    tx_pending_expense = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("250.00"),
        transaction_type=TransactionType.EXPENSE,
        status=TransactionStatus.PENDING,
        transaction_date=now,
        description="Boleto Faculdade",
        source_account_id=sample_account.id,
    )
    tx_pending_income = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("100.00"),
        transaction_type=TransactionType.INCOME,
        status=TransactionStatus.PENDING,
        transaction_date=now,
        description="Reembolso",
        source_account_id=sample_account.id,
    )
    transaction_repo.list_pending_by_user.return_value = [
        tx_pending_expense,
        tx_pending_income,
    ]

    use_case = GetDashboardProjectionsUseCase(account_repo, transaction_repo)
    payload = GetDashboardProjectionsInput(user_id=sample_account.user_id)

    result = await use_case.execute(payload)

    assert result["total_current_balance"] == "1000.00"
    assert result["total_pending_income"] == "100.00"
    assert result["total_pending_expense"] == "250.00"
    # 1000.00 + 100.00 - 250.00 = 850.00
    assert result["total_projected_balance"] == "850.00"

    acc_proj = result["accounts"][0]
    assert acc_proj["current_balance"] == "1000.00"
    assert acc_proj["pending_income"] == "100.00"
    assert acc_proj["pending_expense"] == "250.00"
    assert acc_proj["projected_balance"] == "850.00"
    assert acc_proj["is_projected_negative"] is False


@pytest.mark.anyio
async def test_dashboard_projections_negative_balance(mock_repos, sample_account):
    account_repo, transaction_repo = mock_repos
    sample_account.balance = Decimal("200.00")
    account_repo.list_all.return_value = [sample_account]

    now = datetime.now(UTC)
    tx_huge_expense = Transaction(
        id=uuid.uuid4(),
        user_id=sample_account.user_id,
        amount=Decimal("500.00"),
        transaction_type=TransactionType.EXPENSE,
        status=TransactionStatus.PENDING,
        transaction_date=now,
        description="IPVA",
        source_account_id=sample_account.id,
    )
    transaction_repo.list_pending_by_user.return_value = [tx_huge_expense]

    use_case = GetDashboardProjectionsUseCase(account_repo, transaction_repo)
    payload = GetDashboardProjectionsInput(user_id=sample_account.user_id)

    result = await use_case.execute(payload)

    assert result["total_current_balance"] == "200.00"
    assert result["total_projected_balance"] == "-300.00"

    acc_proj = result["accounts"][0]
    assert acc_proj["projected_balance"] == "-300.00"
    assert acc_proj["is_projected_negative"] is True
