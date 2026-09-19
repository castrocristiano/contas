import calendar
from datetime import UTC, datetime
from decimal import Decimal

from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlmodel import select

from contas.db.session import get_session
from contas.models.budget import Budget
from contas.models.category import Category, CategoryType
from contas.models.transaction import Transaction, TransactionStatus, TransactionType
from contas.schemas.budget import (
    BudgetItemStatus,
    BudgetPeriod,
    BudgetResponse,
    BudgetStatusResponse,
    BudgetSummary,
    GetBudgetStatusInput,
    SetBudgetInput,
)
from contas.tools.errors import (
    CategoryNotFoundError,
    ContasError,
    DatabaseError,
    IntegrityError,
    ValidationError,
)


def register_budget_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def set_budget(payload: SetBudgetInput) -> dict:
        """Set or update a monthly budget limit for an expense category."""
        try:
            async with get_session() as session:
                category = (
                    await session.exec(
                        select(Category).where(
                            Category.id == payload.category_id,
                            Category.is_active == True,
                        )
                    )
                ).first()
                if not category:
                    raise CategoryNotFoundError(str(payload.category_id))

                if category.category_type != CategoryType.EXPENSE:
                    raise ValidationError(
                        f"Category '{category.name}' is of type '{category.category_type}'. Budgets can only be set for expense categories."
                    )

                existing_budget = (
                    await session.exec(
                        select(Budget).where(
                            Budget.category_id == payload.category_id,
                            Budget.month == payload.month,
                            Budget.year == payload.year,
                        )
                    )
                ).first()

                budget_amount = Decimal(payload.amount)

                if existing_budget:
                    existing_budget.amount = budget_amount
                    session.add(existing_budget)
                    await session.commit()
                    await session.refresh(existing_budget)
                    budget = existing_budget
                else:
                    budget = Budget(
                        category_id=payload.category_id,
                        amount=budget_amount,
                        month=payload.month,
                        year=payload.year,
                        created_at=datetime.now(UTC),
                    )
                    session.add(budget)
                    await session.commit()
                    await session.refresh(budget)

            response = BudgetResponse(
                id=budget.id,
                category_id=budget.category_id,
                category_name=category.name,
                amount=f"{budget.amount:.2f}",
                month=budget.month,
                year=budget.year,
                created_at=budget.created_at,
            )
            return response.model_dump(mode="json")
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_budget_status(payload: GetBudgetStatusInput) -> dict:
        """Get budget execution and consumption metrics for a specific month and year."""
        try:
            now = datetime.now(UTC)
            target_month = payload.month if payload.month is not None else now.month
            target_year = payload.year if payload.year is not None else now.year

            _, last_day = calendar.monthrange(target_year, target_month)
            start_date = datetime(target_year, target_month, 1, 0, 0, 0, tzinfo=UTC)
            end_date = datetime(
                target_year, target_month, last_day, 23, 59, 59, 999999, tzinfo=UTC
            )

            async with get_session() as session:
                budget_query = select(Budget).where(
                    Budget.month == target_month,
                    Budget.year == target_year,
                )
                if payload.category_id is not None:
                    budget_query = budget_query.where(
                        Budget.category_id == payload.category_id
                    )

                budgets = (await session.exec(budget_query)).all()

                # Pre-fetch categories
                cat_ids = [b.category_id for b in budgets]
                categories_map: dict = {}
                if cat_ids:
                    cats = (
                        await session.exec(
                            select(Category).where(Category.id.in_(cat_ids))
                        )
                    ).all()
                    categories_map = {c.id: c for c in cats}

                # Pre-fetch transactions for these categories in the period
                tx_query = select(Transaction).where(
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.status == TransactionStatus.CLEARED,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
                if payload.category_id is not None:
                    tx_query = tx_query.where(
                        Transaction.category_id == payload.category_id
                    )
                elif cat_ids:
                    tx_query = tx_query.where(Transaction.category_id.in_(cat_ids))
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
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
