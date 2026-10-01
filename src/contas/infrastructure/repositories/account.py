from uuid import UUID

from sqlmodel import select

from contas.application.ports.repositories import IAccountRepository
from contas.db.session import get_session
from contas.domain.entities import Account as DomainAccount
from contas.domain.enums import AccountType
from contas.domain.errors import AccountNotFoundError
from contas.models.account import Account as ORMAccount
from contas.models.transaction import Transaction as ORMTransaction


class SQLAlchemyAccountRepository(IAccountRepository):
    def _to_domain(self, orm: ORMAccount) -> DomainAccount:
        return DomainAccount(
            id=orm.id,
            name=orm.name,
            account_type=AccountType(orm.account_type),
            balance=orm.balance,
            currency=orm.currency,
            is_active=orm.is_active,
            created_at=orm.created_at,
        )

    async def get_by_id(
        self, account_id: UUID, only_active: bool = True
    ) -> DomainAccount | None:
        async with get_session() as session:
            query = select(ORMAccount).where(ORMAccount.id == account_id)
            if only_active:
                query = query.where(ORMAccount.is_active == True)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def list_all(
        self,
        only_active: bool = True,
        account_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DomainAccount]:
        async with get_session() as session:
            query = select(ORMAccount)
            if only_active:
                query = query.where(ORMAccount.is_active == True)
            if account_type:
                query = query.where(ORMAccount.account_type == account_type)
            query = query.offset(offset).limit(limit)
            results = (await session.exec(query)).all()
            return [self._to_domain(acc) for acc in results]

    async def create(self, account: DomainAccount) -> DomainAccount:
        async with get_session() as session:
            orm = ORMAccount(
                id=account.id,
                name=account.name,
                account_type=account.account_type,
                balance=account.balance,
                currency=account.currency,
                is_active=account.is_active,
                created_at=account.created_at,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)

    async def update(self, account: DomainAccount) -> DomainAccount:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMAccount).where(ORMAccount.id == account.id)
                )
            ).first()
            if not orm:
                raise AccountNotFoundError(str(account.id))
            orm.name = account.name
            orm.account_type = account.account_type
            orm.balance = account.balance
            orm.currency = account.currency
            orm.is_active = account.is_active
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)

    async def delete(self, account_id: UUID) -> bool:
        async with get_session() as session, session.begin():
            orm = (
                await session.exec(
                    select(ORMAccount).where(ORMAccount.id == account_id)
                )
            ).first()
            if not orm:
                return False
            # remove transactions referencing account
            tx_stmt = select(ORMTransaction).where(
                (ORMTransaction.source_account_id == account_id)
                | (ORMTransaction.destination_account_id == account_id)
            )
            txs = (await session.exec(tx_stmt)).all()
            for tx in txs:
                await session.delete(tx)
            await session.delete(orm)
            return True

    async def bulk_delete(self, account_ids: list[UUID], cascade: bool = False) -> int:
        if not account_ids:
            return 0
        deleted_count = 0
        async with get_session() as session, session.begin():
            for acc_id in account_ids:
                acc = (
                    await session.exec(
                        select(ORMAccount).where(ORMAccount.id == acc_id)
                    )
                ).first()
                if not acc:
                    continue

                tx_stmt = select(ORMTransaction).where(
                    (ORMTransaction.source_account_id == acc_id)
                    | (ORMTransaction.destination_account_id == acc_id)
                )
                transactions = (await session.exec(tx_stmt)).all()

                if transactions and not cascade:
                    acc.is_active = False
                    session.add(acc)
                else:
                    if transactions and cascade:
                        for tx in transactions:
                            await session.delete(tx)
                    await session.delete(acc)
                deleted_count += 1
        return deleted_count
