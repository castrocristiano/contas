from uuid import UUID, uuid4

import pytest

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.ui.services import UIService


@pytest.mark.anyio
async def test_ui_service_accounts_and_categories():
    # 1. Create account
    acc_name = f"UI Conta {uuid4().hex[:8]}"
    acc = UIService.create_account(
        name=acc_name,
        account_type=AccountType.CHECKING,
        initial_balance="1500.00",
    )
    assert "id" in acc
    assert acc["name"] == acc_name

    # 2. List accounts
    accs = UIService.list_accounts()
    assert "accounts" in accs
    assert any(a["id"] == acc["id"] for a in accs["accounts"])

    # 3. Create category
    cat_name = f"UI Categoria {uuid4().hex[:8]}"
    cat = UIService.create_category(
        name=cat_name,
        category_type=CategoryType.EXPENSE,
    )
    assert "id" in cat

    # 4. List categories
    cats = UIService.list_categories(category_type=CategoryType.EXPENSE)
    assert any(c["id"] == cat["id"] for c in cats["categories"])


@pytest.mark.anyio
async def test_ui_service_bulk_delete_accounts():

    acc_1 = UIService.create_account(
        name=f"Bulk 1 {uuid4().hex[:6]}",
        account_type=AccountType.CHECKING,
        initial_balance="0.00",
    )
    acc_2 = UIService.create_account(
        name=f"Bulk 2 {uuid4().hex[:6]}",
        account_type=AccountType.SAVINGS,
        initial_balance="0.00",
    )

    ids = [acc_1["id"], acc_2["id"]]
    results = [
        UIService.delete_account(account_id=UUID(a_id), force_cascade=True)
        for a_id in ids
    ]
    assert all("error" not in r for r in results)


@pytest.mark.anyio
async def test_ui_service_bulk_delete_transactions():

    acc = UIService.create_account(
        name=f"Tx Acc {uuid4().hex[:6]}",
        account_type=AccountType.CHECKING,
        initial_balance="1000.00",
    )
    acc_id = UUID(acc["id"])

    t1 = UIService.record_transaction(
        amount="50.00",
        transaction_type="expense",
        source_account_id=acc_id,
        description="Tx 1",
    )
    t2 = UIService.record_transaction(
        amount="30.00",
        transaction_type="expense",
        source_account_id=acc_id,
        description="Tx 2",
    )

    t_ids = [t1["id"], t2["id"]]
    results = [UIService.delete_transaction(transaction_id=UUID(tid)) for tid in t_ids]
    assert all("error" not in r for r in results)

    # Clean up account
    UIService.delete_account(account_id=acc_id, force_cascade=True)


@pytest.mark.anyio
async def test_ui_service_record_transaction_with_status_and_installment(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    from contas.models.transaction import TransactionStatus
    from contas.schemas.transaction import RecordTransactionInput

    mock_server = MagicMock()
    mock_fn = AsyncMock()
    mock_fn.return_value = {
        "id": str(uuid4()),
        "status": "pending",
        "amount": "120.00",
        "total_installments": 5,
        "installment_number": 3,
    }
    mock_server._tool_manager._tools = {"record_transaction": MagicMock(fn=mock_fn)}
    monkeypatch.setattr("contas.ui.services.get_mcp_server", lambda: mock_server)

    acc_id = uuid4()
    t_pending = UIService.record_transaction(
        amount="120.00",
        transaction_type="expense",
        source_account_id=acc_id,
        description="Compra Futura Parcela 3/5",
        status=TransactionStatus.PENDING.value,
        total_installments=5,
        installment_number=3,
    )

    assert "error" not in t_pending
    assert t_pending["status"] == "pending"

    # Verify handler received correct RecordTransactionInput
    call_args = mock_fn.call_args
    assert call_args is not None
    payload: RecordTransactionInput = call_args.kwargs["payload"]
    assert payload.amount == "120.00"
    assert payload.status == TransactionStatus.PENDING
    assert payload.total_installments == 5
    assert payload.installment_number == 3
    assert payload.source_account_id == acc_id
