from uuid import uuid4

import pytest

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.models.transaction import TransactionType
from contas.schemas.account import CreateAccountInput
from contas.schemas.budget import GetBudgetStatusInput, SetBudgetInput
from contas.schemas.category import CreateCategoryInput
from contas.schemas.transaction import RecordTransactionInput
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_budget_execution_within_and_exceeded(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    create_category_handler = server._tool_manager._tools["create_category"].fn
    set_budget_handler = server._tool_manager._tools["set_budget"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    budget_status_handler = server._tool_manager._tools["get_budget_status"].fn

    # 1. Create account
    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Teste Orçamento {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="2000.00",
        )
    )
    acc_id = account["id"]

    # 2. Create category
    category = await create_category_handler(
        payload=CreateCategoryInput(
            name=f"Mercado Execução {uuid4().hex[:8]}",
            category_type=CategoryType.EXPENSE,
        )
    )
    cat_id = category["id"]

    # 3. Set budget for 09/2026: R$ 500.00
    await set_budget_handler(
        payload=SetBudgetInput(
            category_id=cat_id,
            amount="500.00",
            month=9,
            year=2026,
        )
    )

    # 4. Status with 0 expenses
    status_0 = await budget_status_handler(
        payload=GetBudgetStatusInput(
            category_id=cat_id,
            month=9,
            year=2026,
        )
    )
    assert status_0["summary"]["total_budgeted"] == "500.00"
    assert status_0["summary"]["total_spent"] == "0.00"
    assert status_0["summary"]["total_remaining"] == "500.00"
    assert status_0["summary"]["overall_percentage"] == "0.00"
    item_0 = status_0["budgets"][0]
    assert item_0["is_exceeded"] is False
    assert item_0["remaining_balance"] == "500.00"

    # 5. Record expense of R$ 350.00 on 2026-09-10
    await record_tx_handler(
        payload=RecordTransactionInput(
            amount="350.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            category_id=cat_id,
            description="Compras da semana",
            transaction_date="2026-09-10T12:00:00Z",
        )
    )

    # Check status: 350 spent, 150 remaining, 70%
    status_1 = await budget_status_handler(
        payload=GetBudgetStatusInput(
            category_id=cat_id,
            month=9,
            year=2026,
        )
    )
    item_1 = status_1["budgets"][0]
    assert item_1["budget_amount"] == "500.00"
    assert item_1["spent_amount"] == "350.00"
    assert item_1["remaining_balance"] == "150.00"
    assert item_1["spent_percentage"] == "70.00"
    assert item_1["is_exceeded"] is False

    # 6. Record another expense of R$ 200.00 -> total 550.00 (exceeded!)
    await record_tx_handler(
        payload=RecordTransactionInput(
            amount="200.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            category_id=cat_id,
            description="Compras extras",
            transaction_date="2026-09-20T12:00:00Z",
        )
    )

    status_2 = await budget_status_handler(
        payload=GetBudgetStatusInput(
            category_id=cat_id,
            month=9,
            year=2026,
        )
    )
    item_2 = status_2["budgets"][0]
    assert item_2["budget_amount"] == "500.00"
    assert item_2["spent_amount"] == "550.00"
    assert item_2["remaining_balance"] == "-50.00"
    assert item_2["spent_percentage"] == "110.00"
    assert item_2["is_exceeded"] is True
