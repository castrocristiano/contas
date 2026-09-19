import pytest
from pydantic import ValidationError

from contas.models.category import CategoryType
from contas.schemas.category import CreateCategoryInput, ListCategoriesInput


def test_create_category_input_valid():
    payload = CreateCategoryInput(
        name="Supermercado",
        category_type=CategoryType.EXPENSE,
    )
    assert payload.name == "Supermercado"
    assert payload.category_type == CategoryType.EXPENSE


def test_create_category_input_rejects_empty_name():
    with pytest.raises(ValidationError):
        CreateCategoryInput(
            name="",
            category_type=CategoryType.EXPENSE,
        )


def test_create_category_input_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        CreateCategoryInput(
            name="Lazer",
            category_type=CategoryType.EXPENSE,
            unexpected_field="invalid",
        )


def test_list_categories_input_default():
    payload = ListCategoriesInput()
    assert payload.category_type is None
    assert payload.include_inactive is False


def test_list_categories_input_filter():
    payload = ListCategoriesInput(
        category_type=CategoryType.INCOME,
        include_inactive=True,
    )
    assert payload.category_type == CategoryType.INCOME
    assert payload.include_inactive is True
