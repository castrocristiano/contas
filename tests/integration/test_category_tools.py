from uuid import uuid4

import pytest

from contas.models.category import CategoryType
from contas.schemas.category import CreateCategoryInput, ListCategoriesInput
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_create_category_success_and_duplicate(server):
    create_handler = server._tool_manager._tools["create_category"].fn
    list_handler = server._tool_manager._tools["list_categories"].fn

    category_name = f"Categoria Teste Única {uuid4().hex[:8]}"

    # Create category
    res = await create_handler(
        payload=CreateCategoryInput(
            name=category_name,
            category_type=CategoryType.EXPENSE,
        )
    )
    assert "id" in res
    assert res["name"] == category_name
    assert res["category_type"] == "expense"
    assert res["is_active"] is True

    # Duplicate should return structured error
    dup_res = await create_handler(
        payload=CreateCategoryInput(
            name=category_name,
            category_type=CategoryType.EXPENSE,
        )
    )
    assert "error" in dup_res
    assert dup_res["error"]["code"] == "CATEGORY_ALREADY_EXISTS"

    # List categories
    list_res = await list_handler(
        payload=ListCategoriesInput(
            category_type=CategoryType.EXPENSE,
        )
    )
    assert "categories" in list_res
    names = [c["name"] for c in list_res["categories"]]
    assert category_name in names
