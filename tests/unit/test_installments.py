from datetime import UTC, datetime
from decimal import Decimal

import pytest

from contas.utils.installments import add_months, calculate_installments


def test_calculate_installments_exact_division():
    total = Decimal("300.00")
    parts = calculate_installments(total, 3)
    assert len(parts) == 3
    assert parts == [Decimal("100.00"), Decimal("100.00"), Decimal("100.00")]
    assert sum(parts) == total


def test_calculate_installments_with_cents_remainder():
    total = Decimal("100.00")
    parts = calculate_installments(total, 3)
    assert len(parts) == 3
    assert parts == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(parts) == total


def test_calculate_installments_single_installment():
    total = Decimal("49.90")
    parts = calculate_installments(total, 1)
    assert parts == [Decimal("49.90")]


def test_calculate_installments_invalid_count():
    with pytest.raises(ValueError):
        calculate_installments(Decimal("100.00"), 0)


def test_add_months_regular():
    dt = datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC)
    res = add_months(dt, 2)
    assert res == datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC)


def test_add_months_year_rollover():
    dt = datetime(2026, 11, 10, 10, 0, 0, tzinfo=UTC)
    res = add_months(dt, 3)
    assert res == datetime(2027, 2, 10, 10, 0, 0, tzinfo=UTC)


def test_add_months_end_of_month_adjustment():
    # 31 Jan -> 28 Feb in non-leap year (2026)
    dt = datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)
    res = add_months(dt, 1)
    assert res == datetime(2026, 2, 28, 12, 0, 0, tzinfo=UTC)

    # 31 Jan -> 30 Apr
    res_apr = add_months(dt, 3)
    assert res_apr == datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)
