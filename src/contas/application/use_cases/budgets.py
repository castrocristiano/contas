import calendar
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from contas.application.ports.repositories import (
    IBudgetRepository,
    ICategoryRepository,
)
from contas.domain.entities import Budget
from contas.domain.enums import CategoryType
from contas.domain.errors import CategoryNotFoundError, ValidationError
from contas.schemas.budget import (
    BudgetItemStatus,
    BudgetPeriod,
    BudgetResponse,
    BudgetStatusResponse,
    BudgetSummary,
    GetBudgetStatusInput,
    SetBudgetInput,
)


class SetBudgetUseCase:
    def __init__(
        self,
        budget_repo: IBudgetRepository,
        category_repo: ICategoryRepository,
    ) -> None:
        self.budget_repo = budget_repo
        self.category_repo = category_repo

    async def execute(self, payload: SetBudgetInput) -> dict[str, Any]:
        category = await self.category_repo.get_by_id(
            payload.category_id, only_active=True
        )
        if not category:
            raise CategoryNotFoundError(str(payload.category_id))

        if category.category_type != CategoryType.EXPENSE:
            raise ValidationError(
                f"Category '{category.name}' is of type '{category.category_type}'. Budgets can only be set for expense categories."
            )

        budget_amount = Decimal(payload.amount)
        budget = Budget(
            category_id=payload.category_id,
            amount=budget_amount,
            month=payload.month,
            year=payload.year,
        )
        saved = await self.budget_repo.set_budget(budget)
        response = BudgetResponse(
            id=saved.id,
            category_id=saved.category_id,
            category_name=category.name,
            amount=f"{saved.amount:.2f}",
            month=saved.month,
            year=saved.year,
            created_at=saved.created_at,
        )
        return response.model_dump(mode="json")


class GetBudgetStatusUseCase:
    def __init__(
        self,
        budget_repo: IBudgetRepository,
        category_repo: ICategoryRepository,
    ) -> None:
        self.budget_repo = budget_repo
        self.category_repo = category_repo

    async def execute(self, payload: GetBudgetStatusInput) -> dict[str, Any]:
        from sqlmodel import select

        from contas.db.session import get_session
        from contas.models.budget import Budget as ORMBudget
        from contas.models.category import Category as ORMCategory
        from contas.models.transaction import Transaction as ORMTransaction
        from contas.models.transaction import TransactionStatus, TransactionType

        now = datetime.now(UTC)
        target_month = payload.month if payload.month is not None else now.month
        target_year = payload.year if payload.year is not None else now.year

        _, last_day = calendar.monthrange(target_year, target_month)
        start_date = datetime(target_year, target_month, 1, 0, 0, 0, tzinfo=UTC)
        end_date = datetime(
            target_year, target_month, last_day, 23, 59, 59, 999999, tzinfo=UTC
        )

        async with get_session() as session:
            budget_query = select(ORMBudget).where(
                ORMBudget.month == target_month,
                ORMBudget.year == target_year,
            )
            if payload.category_id is not None:
                budget_query = budget_query.where(
                    ORMBudget.category_id == payload.category_id
                )

            budgets = (await session.exec(budget_query)).all()

            cat_ids = [b.category_id for b in budgets]
            categories_map: dict = {}
            if cat_ids:
                cats = (
                    await session.exec(
                        select(ORMCategory).where(ORMCategory.id.in_(cat_ids))
                    )
                ).all()
                categories_map = {c.id: c for c in cats}

            tx_query = select(ORMTransaction).where(
                ORMTransaction.transaction_type == TransactionType.EXPENSE,
                ORMTransaction.status == TransactionStatus.CLEARED,
                ORMTransaction.transaction_date >= start_date,
                ORMTransaction.transaction_date <= end_date,
            )
            if payload.category_id is not None:
                tx_query = tx_query.where(
                    ORMTransaction.category_id == payload.category_id
                )
            elif cat_ids:
                tx_query = tx_query.where(ORMTransaction.category_id.in_(cat_ids))
            else:
                tx_query = tx_query.where(False)

            transactions = (await session.exec(tx_query)).all()

        spent_by_cat: dict = {}
        for tx in transactions:
            if tx.category_id:
                spent_by_cat[tx.category_id] = (
                    spent_by_cat.get(tx.category_id, Decimal("0.00")) + tx.amount
                )

        items: list[BudgetItemStatus] = []
        total_budgeted = Decimal("0.00")
        total_spent = Decimal("0.00")

        for b in budgets:
            cat = categories_map.get(b.category_id)
            cat_name = cat.name if cat else "Desconhecida"
            spent = spent_by_cat.get(b.category_id, Decimal("0.00"))
            remaining = b.amount - spent
            spent_pct = (
                (spent / b.amount) * Decimal(100)
                if b.amount > Decimal("0.00")
                else Decimal("0.00")
            )
            is_exceeded = spent > b.amount

            total_budgeted += b.amount
            total_spent += spent

            items.append(
                BudgetItemStatus(
                    category_id=b.category_id,
                    category_name=cat_name,
                    budget_amount=f"{b.amount:.2f}",
                    spent_amount=f"{spent:.2f}",
                    remaining_balance=f"{remaining:.2f}",
                    spent_percentage=f"{spent_pct:.2f}",
                    is_exceeded=is_exceeded,
                )
            )

        total_remaining = total_budgeted - total_spent
        overall_pct = (
            (total_spent / total_budgeted) * Decimal(100)
            if total_budgeted > Decimal("0.00")
            else Decimal("0.00")
        )

        response = BudgetStatusResponse(
            period=BudgetPeriod(month=target_month, year=target_year),
            budgets=items,
            summary=BudgetSummary(
                total_budgeted=f"{total_budgeted:.2f}",
                total_spent=f"{total_spent:.2f}",
                total_remaining=f"{total_remaining:.2f}",
                overall_percentage=f"{overall_pct:.2f}",
            ),
        )
        return response.model_dump(mode="json")
