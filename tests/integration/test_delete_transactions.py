from uuid import uuid4

import pytest

from contas.models.account import AccountType
from contas.models.transaction import TransactionType
from contas.schemas.account import CreateAccountInput, ListAccountsInput
from contas.schemas.transaction import (
    DeleteTransactionInput,
    GetStatementInput,
    RecordTransactionInput,
)
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_delete_expense_reverts_balance(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_tx_handler = server._tool_manager._tools["delete_transaction"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    # 1. Create account with 500.00
    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Teste {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="500.00",
        )
    )
    acc_id = account["id"]

    # 2. Record expense of 100.00 -> balance becomes 400.00
    tx = await record_tx_handler(
        payload=RecordTransactionInput(
            amount="100.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Supermercado",
        )
    )
    tx_id = tx["id"]

    accounts_res = await list_accounts_handler(payload=ListAccountsInput())
    acc_info = next(a for a in accounts_res["accounts"] if a["id"] == str(acc_id))
    assert acc_info["balance"] == "400.00"

    # 3. Delete transaction -> balance should revert to 500.00
    del_res = await delete_tx_handler(
        payload=DeleteTransactionInput(
            transaction_id=tx_id,
        )
    )
    assert del_res["deleted_count"] == 1
    assert del_res["reverted_amount"] == "100.00"

    accounts_res_after = await list_accounts_handler(payload=ListAccountsInput())
    acc_info_after = next(
        a for a in accounts_res_after["accounts"] if a["id"] == str(acc_id)
    )
    assert acc_info_after["balance"] == "500.00"


@pytest.mark.anyio
async def test_delete_income_reverts_balance(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_tx_handler = server._tool_manager._tools["delete_transaction"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Salário {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="1000.00",
        )
    )
    acc_id = account["id"]

    tx = await record_tx_handler(
        payload=RecordTransactionInput(
            amount="250.00",
            transaction_type=TransactionType.INCOME,
            source_account_id=acc_id,
            description="Freela",
        )
    )
    tx_id = tx["id"]

    accounts_res = await list_accounts_handler(payload=ListAccountsInput())
    acc_info = next(a for a in accounts_res["accounts"] if a["id"] == str(acc_id))
    assert acc_info["balance"] == "1250.00"

    del_res = await delete_tx_handler(
        payload=DeleteTransactionInput(transaction_id=tx_id)
    )
    assert del_res["deleted_count"] == 1
    assert del_res["reverted_amount"] == "250.00"

    accounts_res_after = await list_accounts_handler(payload=ListAccountsInput())
    acc_info_after = next(
        a for a in accounts_res_after["accounts"] if a["id"] == str(acc_id)
    )
    assert acc_info_after["balance"] == "1000.00"


@pytest.mark.anyio
async def test_delete_transfer_reverts_both_balances(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_tx_handler = server._tool_manager._tools["delete_transaction"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    acc1 = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Origem {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="1000.00",
        )
    )
    acc2 = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Destino {uuid4().hex[:8]}",
            account_type=AccountType.SAVINGS,
            initial_balance="200.00",
        )
    )

    tx = await record_tx_handler(
        payload=RecordTransactionInput(
            amount="300.00",
            transaction_type=TransactionType.TRANSFER,
            source_account_id=acc1["id"],
            destination_account_id=acc2["id"],
            description="Transferência Poupança",
        )
    )
    tx_id = tx["id"]

    # Verify transferred balances: acc1=700, acc2=500
    res = await list_accounts_handler(payload=ListAccountsInput())
    a1 = next(a for a in res["accounts"] if a["id"] == str(acc1["id"]))
    a2 = next(a for a in res["accounts"] if a["id"] == str(acc2["id"]))
    assert a1["balance"] == "700.00"
    assert a2["balance"] == "500.00"

    # Delete transfer
    del_res = await delete_tx_handler(
        payload=DeleteTransactionInput(transaction_id=tx_id)
    )
    assert del_res["deleted_count"] == 1
    assert del_res["reverted_amount"] == "300.00"

    # Verify reverted balances: acc1=1000, acc2=200
    res_after = await list_accounts_handler(payload=ListAccountsInput())
    a1_after = next(a for a in res_after["accounts"] if a["id"] == str(acc1["id"]))
    a2_after = next(a for a in res_after["accounts"] if a["id"] == str(acc2["id"]))
    assert a1_after["balance"] == "1000.00"
    assert a2_after["balance"] == "200.00"


@pytest.mark.anyio
async def test_delete_installment_all_vs_single(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_tx_handler = server._tool_manager._tools["delete_transaction"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn
    get_statement_handler = server._tool_manager._tools["get_statement"].fn

    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Cartão {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="1000.00",
        )
    )
    acc_id = account["id"]

    # 100 in 3 installments -> 33.34 cleared, two 33.33 pending
    tx_res = await record_tx_handler(
        payload=RecordTransactionInput(
            amount="100.00",
            total_amount="100.00",
            total_installments=3,
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Celular",
        )
    )
    first_tx_id = tx_res["id"]

    # Balance is 1000 - 33.34 = 966.66
    res = await list_accounts_handler(payload=ListAccountsInput())
    acc_info = next(a for a in res["accounts"] if a["id"] == str(acc_id))
    assert acc_info["balance"] == "966.66"

    # Delete with delete_all_installments=True
    del_res = await delete_tx_handler(
        payload=DeleteTransactionInput(
            transaction_id=first_tx_id,
            delete_all_installments=True,
        )
    )
    assert del_res["deleted_count"] == 3
    assert del_res["reverted_amount"] == "33.34"  # Only 1 was cleared!

    # Balance should return to 1000.00
    res_after = await list_accounts_handler(payload=ListAccountsInput())
    acc_info_after = next(a for a in res_after["accounts"] if a["id"] == str(acc_id))
    assert acc_info_after["balance"] == "1000.00"

    # Statement should be empty
    statement = await get_statement_handler(
        payload=GetStatementInput(
            account_id=acc_id,
            start_date="2020-01-01",
            end_date="2030-01-01",
            include_pending=True,
        )
    )
    assert len(statement["transactions"]) == 0


@pytest.mark.anyio
async def test_delete_nonexistent_transaction_returns_error(server):
    delete_tx_handler = server._tool_manager._tools["delete_transaction"].fn

    fake_id = uuid4()
    del_res = await delete_tx_handler(
        payload=DeleteTransactionInput(transaction_id=fake_id)
    )
    assert "error" in del_res
    assert del_res["error"]["code"] == "TRANSACTION_NOT_FOUND"
