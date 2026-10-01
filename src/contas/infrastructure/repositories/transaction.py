from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import select

from contas.application.ports.repositories import ITransactionRepository
from contas.db.session import get_session
from contas.domain.entities import Transaction as DomainTransaction
from contas.domain.enums import TransactionStatus, TransactionType
from contas.models.transaction import Transaction as ORMTransaction


class SQLAlchemyTransactionRepository(ITransactionRepository):
    def _to_domain(self, orm: ORMTransaction) -> DomainTransaction:
        return DomainTransaction(
            id=orm.id,
            amount=orm.amount,
            transaction_type=TransactionType(orm.transaction_type),
            status=TransactionStatus(orm.status),
            transaction_date=orm.transaction_date,
            due_date=orm.due_date,
            description=orm.description,
            source_account_id=orm.source_account_id,
            destination_account_id=orm.destination_account_id,
            category_id=orm.category_id,
            installment_id=orm.installment_id,
            installment_number=orm.installment_number,
            total_installments=orm.total_installments,
            created_at=orm.created_at,
        )

    async def get_by_id(self, transaction_id: UUID) -> DomainTransaction | None:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMTransaction).where(ORMTransaction.id == transaction_id)
                )
            ).first()
            return self._to_domain(orm) if orm else None

    async def create(self, transaction: DomainTransaction) -> DomainTransaction:
        async with get_session() as session:
            orm = ORMTransaction(
                id=transaction.id,
                amount=transaction.amount,
                transaction_type=transaction.transaction_type,
                status=transaction.status,
                transaction_date=transaction.transaction_date,
                due_date=transaction.due_date,
                description=transaction.description,
                source_account_id=transaction.source_account_id,
                destination_account_id=transaction.destination_account_id,
                category_id=transaction.category_id,
                installment_id=transaction.installment_id,
                installment_number=transaction.installment_number,
                total_installments=transaction.total_installments,
                created_at=transaction.created_at,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)

    async def create_many(
        self, transactions: list[DomainTransaction]
    ) -> list[DomainTransaction]:
        if not transactions:
            return []
        async with get_session() as session:
            orm_list = [
                ORMTransaction(
                    id=tx.id,
                    amount=tx.amount,
                    transaction_type=tx.transaction_type,
                    status=tx.status,
                    transaction_date=tx.transaction_date,
                    due_date=tx.due_date,
                    description=tx.description,
                    source_account_id=tx.source_account_id,
                    destination_account_id=tx.destination_account_id,
                    category_id=tx.category_id,
                    installment_id=tx.installment_id,
                    installment_number=tx.installment_number,
                    total_installments=tx.total_installments,
                    created_at=tx.created_at,
                )
                for tx in transactions
            ]
            for orm in orm_list:
                session.add(orm)
            await session.commit()
            for orm in orm_list:
                await session.refresh(orm)
            return [self._to_domain(orm) for orm in orm_list]

    async def delete(self, transaction_id: UUID) -> bool:
        async with get_session() as session, session.begin():
            orm = (
                await session.exec(
                    select(ORMTransaction).where(ORMTransaction.id == transaction_id)
                )
            ).first()
            if not orm:
                return False
            await session.delete(orm)
            return True

    async def bulk_delete(self, transaction_ids: list[UUID]) -> int:
        if not transaction_ids:
            return 0
        deleted = 0
        async with get_session() as session, session.begin():
            for tid in transaction_ids:
                orm = (
                    await session.exec(
                        select(ORMTransaction).where(ORMTransaction.id == tid)
                    )
                ).first()
                if orm:
                    await session.delete(orm)
                    deleted += 1
        return deleted

    async def list_by_account(
        self,
        account_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_type: str = "transaction_date",
        limit: int = 50,
        offset: int = 0,
    ) -> list[DomainTransaction]:
        async with get_session() as session:
            query = select(ORMTransaction).where(
                ORMTransaction.source_account_id == account_id
            )
            date_col = (
                ORMTransaction.due_date
                if date_type == "due_date"
                else ORMTransaction.transaction_date
            )
            if start_date:
                query = query.where(date_col >= start_date)
            if end_date:
                query = query.where(date_col <= end_date)
            query = query.order_by(date_col.asc()).offset(offset).limit(limit)
            results = (await session.exec(query)).all()
            return [self._to_domain(t) for t in results]

    async def list_by_installment_id(
        self, installment_id: UUID
    ) -> list[DomainTransaction]:
        async with get_session() as session:
            query = (
                select(ORMTransaction)
                .where(ORMTransaction.installment_id == installment_id)
                .order_by(ORMTransaction.installment_number.asc())
            )
            results = (await session.exec(query)).all()
            return [self._to_domain(t) for t in results]

    async def delete_by_installment_id(
        self, installment_id: UUID
    ) -> list[DomainTransaction]:
        async with get_session() as session, session.begin():
            query = select(ORMTransaction).where(
                ORMTransaction.installment_id == installment_id
            )
            results = (await session.exec(query)).all()
            for tx in results:
                await session.delete(tx)
            return [self._to_domain(t) for t in results]

    async def count_by_account(self, account_id: UUID) -> int:
        async with get_session() as session:
            tx_stmt = select(ORMTransaction).where(
                (ORMTransaction.source_account_id == account_id)
                | (ORMTransaction.destination_account_id == account_id)
            )
            results = (await session.exec(tx_stmt)).all()
            return len(results)

    async def get_summary_by_account(
        self,
        account_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_type: str = "transaction_date",
    ) -> dict[str, Decimal]:
        txs = await self.list_by_account(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            date_type=date_type,
            limit=10000,
        )
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        for tx in txs:
            if tx.transaction_type == TransactionType.INCOME:
                total_income += tx.amount
            elif tx.transaction_type in (
                TransactionType.EXPENSE,
                TransactionType.TRANSFER,
            ):
                total_expense += tx.amount
        return {
            "income": total_income,
            "expense": total_expense,
            "net": total_income - total_expense,
        }
