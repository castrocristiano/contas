from uuid import uuid4

import pytest

from contas.models.account import AccountType
from contas.models.transaction import TransactionType
from contas.schemas.account import (
    CreateAccountInput,
    DeleteAccountInput,
    ListAccountsInput,
)
from contas.schemas.transaction import RecordTransactionInput
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_delete_account_without_transactions_is_deleted(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    delete_account_handler = server._tool_manager._tools["delete_account"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    # 1. Create account
    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Sem Uso {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="0.00",
        )
    )
    acc_id = account["id"]

    # 2. Delete account
    del_res = await delete_account_handler(
        payload=DeleteAccountInput(account_id=acc_id)
    )
    assert del_res["action_taken"] == "deleted"

    # 3. Should not appear in list even with include_inactive=True
    accounts_res = await list_accounts_handler(
        payload=ListAccountsInput(include_inactive=True)
    )
    assert not any(a["id"] == str(acc_id) for a in accounts_res["accounts"])


@pytest.mark.anyio
async def test_delete_account_with_transactions_deactivates_soft_delete(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_account_handler = server._tool_manager._tools["delete_account"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    # 1. Create account and add a transaction
    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Com Histórico {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="100.00",
        )
    )
    acc_id = account["id"]

    await record_tx_handler(
        payload=RecordTransactionInput(
            amount="20.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Padaria",
        )
    )

    # 2. Delete without force_cascade -> Should deactivate (soft-delete)
    del_res = await delete_account_handler(
        payload=DeleteAccountInput(account_id=acc_id, force_cascade=False)
    )
    assert del_res["action_taken"] == "deactivated"

    # 3. Should NOT appear in active accounts list
    active_res = await list_accounts_handler(
        payload=ListAccountsInput(include_inactive=False)
    )
    assert not any(a["id"] == str(acc_id) for a in active_res["accounts"])

    # 4. Should appear when include_inactive=True
    all_res = await list_accounts_handler(
        payload=ListAccountsInput(include_inactive=True)
    )
    matched = next(a for a in all_res["accounts"] if a["id"] == str(acc_id))
    assert matched["is_active"] is False


@pytest.mark.anyio
async def test_delete_account_with_transactions_force_cascade(server):
    create_account_handler = server._tool_manager._tools["create_account"].fn
    record_tx_handler = server._tool_manager._tools["record_transaction"].fn
    delete_account_handler = server._tool_manager._tools["delete_account"].fn
    list_accounts_handler = server._tool_manager._tools["list_accounts"].fn

    account = await create_account_handler(
        payload=CreateAccountInput(
            name=f"Conta Para Forçar {uuid4().hex[:8]}",
            account_type=AccountType.CHECKING,
            initial_balance="200.00",
        )
    )
    acc_id = account["id"]

    await record_tx_handler(
        payload=RecordTransactionInput(
            amount="50.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Cinema",
        )
    )

    # Delete with force_cascade=True -> Permanently deletes account & transactions
    del_res = await delete_account_handler(
        payload=DeleteAccountInput(account_id=acc_id, force_cascade=True)
    )
    assert del_res["action_taken"] == "deleted"

    # Not found even in include_inactive
    all_res = await list_accounts_handler(
        payload=ListAccountsInput(include_inactive=True)
    )
    assert not any(a["id"] == str(acc_id) for a in all_res["accounts"])


@pytest.mark.anyio
async def test_delete_nonexistent_account_returns_error(server):
    delete_account_handler = server._tool_manager._tools["delete_account"].fn

    fake_id = uuid4()
    del_res = await delete_account_handler(
        payload=DeleteAccountInput(account_id=fake_id)
    )
    assert "error" in del_res
    assert del_res["error"]["code"] == "ACCOUNT_NOT_FOUND"
