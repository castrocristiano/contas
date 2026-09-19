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
