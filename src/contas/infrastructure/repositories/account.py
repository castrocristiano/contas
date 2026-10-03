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
            user_id=orm.user_id,
            name=orm.name,
            account_type=AccountType(orm.account_type),
            balance=orm.balance,
            currency=orm.currency,
            is_active=orm.is_active,
            created_at=orm.created_at,
        )

    async def get_by_id(
        self, account_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> DomainAccount | None:
        async with get_session() as session:
            query = select(ORMAccount).where(ORMAccount.id == account_id)
            if user_id:
                query = query.where(ORMAccount.user_id == user_id)
            if only_active:
                query = query.where(ORMAccount.is_active == True)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        account_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DomainAccount]:
        async with get_session() as session:
            query = select(ORMAccount)
            if user_id:
                query = query.where(ORMAccount.user_id == user_id)
            if only_active:
                query = query.where(ORMAccount.is_active == True)
            if account_type:
                query = query.where(ORMAccount.account_type == account_type)
            query = query.offset(offset).limit(limit)
            results = (await session.exec(query)).all()
            return [self._to_domain(acc) for acc in results]

    async def create(self, account: DomainAccount) -> DomainAccount:
        async with get_session() as session:
            effective_user_id = account.user_id
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

            orm = ORMAccount(
                id=account.id,
                user_id=effective_user_id,
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
            query = select(ORMAccount).where(ORMAccount.id == account.id)
            if account.user_id:
                query = query.where(ORMAccount.user_id == account.user_id)
            orm = (await session.exec(query)).first()
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

    async def delete(self, account_id: UUID, user_id: UUID | None = None) -> bool:
        async with get_session() as session, session.begin():
            query = select(ORMAccount).where(ORMAccount.id == account_id)
            if user_id:
                query = query.where(ORMAccount.user_id == user_id)
            orm = (await session.exec(query)).first()
            if not orm:
                return False
            # remove transactions referencing account
            tx_stmt = select(ORMTransaction).where(
                (ORMTransaction.source_account_id == account_id)
                | (ORMTransaction.destination_account_id == account_id)
            )
            if user_id:
                tx_stmt = tx_stmt.where(ORMTransaction.user_id == user_id)
            txs = (await session.exec(tx_stmt)).all()
            for tx in txs:
                await session.delete(tx)
            await session.delete(orm)
            return True

    async def bulk_delete(
        self,
        account_ids: list[UUID],
        user_id: UUID | None = None,
        cascade: bool = False,
    ) -> int:
        if not account_ids:
            return 0
        deleted_count = 0
        async with get_session() as session, session.begin():
            for acc_id in account_ids:
                query = select(ORMAccount).where(ORMAccount.id == acc_id)
                if user_id:
                    query = query.where(ORMAccount.user_id == user_id)
                acc = (await session.exec(query)).first()
                if not acc:
                    continue

                tx_stmt = select(ORMTransaction).where(
                    (ORMTransaction.source_account_id == acc_id)
                    | (ORMTransaction.destination_account_id == acc_id)
                )
                if user_id:
                    tx_stmt = tx_stmt.where(ORMTransaction.user_id == user_id)
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
