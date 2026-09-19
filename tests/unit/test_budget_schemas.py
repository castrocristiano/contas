from uuid import uuid4

import pytest
from pydantic import ValidationError

from contas.schemas.budget import SetBudgetInput


def test_set_budget_input_valid():
    payload = SetBudgetInput(
        category_id=uuid4(),
        amount="500.00",
        month=9,
        year=2026,
    )
    assert payload.amount == "500.00"
    assert payload.month == 9
    assert payload.year == 2026


def test_set_budget_input_rejects_zero_or_negative():
    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="0.00",
            month=9,
            year=2026,
        )

    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="-50.00",
            month=9,
            year=2026,
        )


def test_set_budget_input_rejects_invalid_month_or_year():
    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="500.00",
            month=0,
            year=2026,
        )

    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="500.00",
            month=13,
            year=2026,
        )

    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="500.00",
            month=9,
            year=1999,
        )


def test_set_budget_input_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        SetBudgetInput(
            category_id=uuid4(),
            amount="500.00",
            month=9,
            year=2026,
            extra="forbidden",
        )
