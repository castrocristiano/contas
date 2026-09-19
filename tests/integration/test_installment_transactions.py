from uuid import uuid4

import pytest

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.models.transaction import TransactionType
from contas.schemas.account import CreateAccountInput
from contas.schemas.category import CreateCategoryInput
from contas.schemas.transaction import (
    GetInstallmentPlanInput,
    GetStatementInput,
    RecordTransactionInput,
)
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_record_installment_purchase_lifecycle(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    create_category_handler = server._tool_manager._tools["create_category"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    get_statement_handler = server._tool_manager._tools["get_statement"].fn
    get_installment_plan_handler = server._tool_manager._tools["get_installment_plan"].fn

    # 1. Create account with R$ 1000.00
    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Cartão de Crédito {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="1000.00",
        )
    )
    acc_id = account["id"]

    # 2. Create category
    category = await create_category_handler(
        payload=CreateCategoryInput(
            name=f"Eletrônicos {uuid4().hex[:8]}",
            category_type=CategoryType.EXPENSE,
        )
    )
    cat_id = category["id"]

    # 3. Record installment purchase: R$ 100.00 in 3 installments
    # Expected: 33.34 (1st), 33.33 (2nd), 33.33 (3rd)
    tx_res = await record_tx_handler(
        payload=RecordTransactionInput(
            amount="100.00",
            total_amount="100.00",
            total_installments=3,
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            category_id=cat_id,
            description="Smartphone Novo",
            transaction_date="2026-09-15T10:00:00Z",
        )
    )
    assert "id" in tx_res
    assert tx_res["amount"] == "33.34"
    assert tx_res["total_amount"] == "100.00"
    assert tx_res["installment_number"] == 1
    assert tx_res["total_installments"] == 3
    assert tx_res["installment_id"] is not None
    # Account balance debited only by first installment: 1000 - 33.34 = 966.66
    assert tx_res["source_account"]["new_balance"] == "966.66"

    installment_id = tx_res["installment_id"]

    # 4. Query statement with pending transactions
    statement = await get_statement_handler(
        payload=GetStatementInput(
            account_id=acc_id,
            start_date="2026-09-01",
            end_date="2026-11-30",
            include_pending=True,
        )
    )
    assert "transactions" in statement
    # Should contain all 3 installments
    installment_txs = [
        t for t in statement["transactions"] if t.get("installment_id") == installment_id
    ]
    assert len(installment_txs) == 3
    assert [t["amount"] for t in installment_txs] == ["33.34", "33.33", "33.33"]
    assert [t["installment_number"] for t in installment_txs] == [1, 2, 3]
    assert installment_txs[0]["status"] == "cleared"
    assert installment_txs[1]["status"] == "pending"
    assert installment_txs[2]["status"] == "pending"

    # 5. Query installment plan
    plan = await get_installment_plan_handler(
        payload=GetInstallmentPlanInput(
            installment_id=installment_id,
        )
    )
    assert plan["total_amount"] == "100.00"
    assert plan["total_installments"] == 3
    assert plan["paid_amount"] == "33.34"
    assert plan["remaining_amount"] == "66.66"
    assert plan["paid_installments"] == 1
    assert plan["remaining_installments"] == 2
    assert len(plan["installments"]) == 3

