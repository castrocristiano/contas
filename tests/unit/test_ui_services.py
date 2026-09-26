from uuid import uuid4

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
    from uuid import UUID

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
    from uuid import UUID

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
