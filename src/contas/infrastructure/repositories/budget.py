import calendar
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import select

from contas.application.ports.repositories import IBudgetRepository
from contas.db.session import get_session
from contas.domain.entities import Budget as DomainBudget
from contas.domain.enums import TransactionStatus, TransactionType
from contas.models.budget import Budget as ORMBudget
from contas.models.transaction import Transaction as ORMTransaction


class SQLAlchemyBudgetRepository(IBudgetRepository):
    def _to_domain(self, orm: ORMBudget) -> DomainBudget:
        return DomainBudget(
            id=orm.id,
            user_id=orm.user_id,
            category_id=orm.category_id,
            amount=orm.amount,
            month=orm.month,
            year=orm.year,
            created_at=orm.created_at,
        )

    async def get(
        self, category_id: UUID, month: int, year: int, user_id: UUID | None = None
    ) -> DomainBudget | None:
        async with get_session() as session:
            query = select(ORMBudget).where(
                ORMBudget.category_id == category_id,
                ORMBudget.month == month,
                ORMBudget.year == year,
            )
            if user_id:
                query = query.where(ORMBudget.user_id == user_id)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def set_budget(self, budget: DomainBudget) -> DomainBudget:
        async with get_session() as session:
            query = select(ORMBudget).where(
                ORMBudget.category_id == budget.category_id,
                ORMBudget.month == budget.month,
                ORMBudget.year == budget.year,
            )
            if budget.user_id:
                query = query.where(ORMBudget.user_id == budget.user_id)
            existing = (await session.exec(query)).first()
            if existing:
                existing.amount = budget.amount
                session.add(existing)
                await session.commit()
                await session.refresh(existing)
                return self._to_domain(existing)

            effective_user_id = budget.user_id
            if not effective_user_id or effective_user_id == UUID(
                "00000000-0000-0000-0000-000000000000"
            ):
                from contas.models.user import User as ORMUser

                default_user = (
                    await session.exec(
                        select(ORMUser).order_by(ORMUser.created_at.asc()).limit(1)
                    )
                ).first()
                if default_user:
                    effective_user_id = default_user.id

            orm = ORMBudget(
                id=budget.id,
                user_id=effective_user_id,
                category_id=budget.category_id,
                amount=budget.amount,
                month=budget.month,
                year=budget.year,
                created_at=budget.created_at,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)

    async def get_spent_for_category(
        self, category_id: UUID, month: int, year: int, user_id: UUID | None = None
    ) -> Decimal:
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=UTC)
        end_date = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        async with get_session() as session:
            query = select(ORMTransaction).where(
                ORMTransaction.category_id == category_id,
                ORMTransaction.transaction_type == TransactionType.EXPENSE,
                ORMTransaction.status == TransactionStatus.CLEARED,
                ORMTransaction.transaction_date >= start_date,
                ORMTransaction.transaction_date <= end_date,
            )
            if user_id:
                query = query.where(ORMTransaction.user_id == user_id)
            results = (await session.exec(query)).all()
            return sum((tx.amount for tx in results), Decimal("0.00"))
