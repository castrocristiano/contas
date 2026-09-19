from uuid import uuid4

import pytest

from contas.models.category import CategoryType
from contas.schemas.budget import SetBudgetInput
from contas.schemas.category import CreateCategoryInput
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_set_budget_success_and_update(server):
    create_category_handler = server._tool_manager._tools["create_category"].fn
    set_budget_handler = server._tool_manager._tools["set_budget"].fn

    # 1. Create expense category
    cat_name = f"Alimentação Orçamento Teste {uuid4().hex[:8]}"
    cat_res = await create_category_handler(
        payload=CreateCategoryInput(
            name=cat_name,
            category_type=CategoryType.EXPENSE,
        )
    )
    cat_id = cat_res["id"]

    # 2. Set budget
    budget_res = await set_budget_handler(
        payload=SetBudgetInput(
            category_id=cat_id,
            amount="500.00",
            month=9,
            year=2026,
        )
    )
    assert "id" in budget_res
    assert budget_res["amount"] == "500.00"
    assert budget_res["category_name"] == cat_name
    assert budget_res["month"] == 9
    assert budget_res["year"] == 2026

    # 3. Update budget (upsert)
    update_res = await set_budget_handler(
        payload=SetBudgetInput(
            category_id=cat_id,
            amount="750.00",
            month=9,
            year=2026,
        )
    )
    assert update_res["id"] == budget_res["id"]
    assert update_res["amount"] == "750.00"


@pytest.mark.anyio
async def test_set_budget_nonexistent_category(server):
    set_budget_handler = server._tool_manager._tools["set_budget"].fn

    res = await set_budget_handler(
        payload=SetBudgetInput(
            category_id=uuid4(),
            amount="100.00",
            month=9,
            year=2026,
        )
    )
    assert "error" in res
    assert res["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.anyio
async def test_set_budget_rejects_income_category(server):
    create_category_handler = server._tool_manager._tools["create_category"].fn
    set_budget_handler = server._tool_manager._tools["set_budget"].fn

    cat_res = await create_category_handler(
        payload=CreateCategoryInput(
            name=f"Salário Orçamento Teste {uuid4().hex[:8]}",
            category_type=CategoryType.INCOME,
        )
    )
    cat_id = cat_res["id"]

    res = await set_budget_handler(
        payload=SetBudgetInput(
            category_id=cat_id,
            amount="5000.00",
            month=9,
            year=2026,
        )
    )
    assert "error" in res
    assert res["error"]["code"] == "VALIDATION_ERROR"
