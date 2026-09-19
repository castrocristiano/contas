import calendar
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal


def calculate_installments(
    total_amount: Decimal, total_installments: int
) -> list[Decimal]:
    """
    Splits total_amount into total_installments Decimal amounts.
    Any fraction of cents is added to the first installment so that:
    sum(installments) == total_amount.
    """
    if total_installments <= 0:
        raise ValueError("total_installments must be greater than 0")

    # Base installment amount truncated to 2 decimal places
    base = (total_amount / Decimal(total_installments)).quantize(
        Decimal("0.01"), rounding=ROUND_FLOOR
    )
    remainder = total_amount - (base * Decimal(total_installments))

    installments = []
    for i in range(total_installments):
        if i == 0:
            installments.append(base + remainder)
        else:
            installments.append(base)

    return installments


def add_months(source_dt: datetime, months: int) -> datetime:
    """
    Adds a number of months to a datetime, handling end-of-month boundaries safely
    (e.g., 31 Jan + 1 month -> 28/29 Feb).
    """
    month = source_dt.month - 1 + months
    year = source_dt.year + month // 12
    month = month % 12 + 1

    _, last_day = calendar.monthrange(year, month)
    day = min(source_dt.day, last_day)

    return source_dt.replace(year=year, month=month, day=day)
