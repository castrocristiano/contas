from uuid import UUID

from sqlmodel import func, select

from contas.application.ports.repositories import IUserRepository
from contas.db.session import get_session
from contas.domain.entities import User as DomainUser
from contas.models.user import User as ORMUser


class SQLAlchemyUserRepository(IUserRepository):
    def _to_domain(self, orm: ORMUser) -> DomainUser:
        return DomainUser(
            id=orm.id,
            name=orm.name,
            email=orm.email,
            username=orm.username,
            password_hash=orm.password_hash,
            auth_provider=orm.auth_provider,
            google_id=orm.google_id,
            avatar_url=orm.avatar_url,
            is_active=orm.is_active,
            is_approved=orm.is_approved,
            role=orm.role,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def get_by_id(self, user_id: UUID) -> DomainUser | None:
        async with get_session() as session:
            orm = (
                await session.exec(select(ORMUser).where(ORMUser.id == user_id))
            ).first()
            return self._to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> DomainUser | None:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMUser).where(ORMUser.email == email.lower().strip())
                )
            ).first()
            return self._to_domain(orm) if orm else None

    async def get_by_username(self, username: str) -> DomainUser | None:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMUser).where(ORMUser.username == username.lower().strip())
                )
            ).first()
            return self._to_domain(orm) if orm else None

    async def get_by_google_id(self, google_id: str) -> DomainUser | None:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMUser).where(ORMUser.google_id == google_id)
                )
            ).first()
            return self._to_domain(orm) if orm else None

    async def count(self) -> int:
        async with get_session() as session:
            res = (await session.exec(select(func.count(ORMUser.id)))).first()
            return res or 0

    async def get_default_user(self) -> DomainUser | None:
        async with get_session() as session:
            orm = (
                await session.exec(
                    select(ORMUser).order_by(ORMUser.created_at.asc()).limit(1)
                )
            ).first()
            return self._to_domain(orm) if orm else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[DomainUser]:
        async with get_session() as session:
            results = (
                await session.exec(
                    select(ORMUser)
                    .order_by(ORMUser.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
            return [self._to_domain(u) for u in results]

    async def create(self, user: DomainUser) -> DomainUser:
        async with get_session() as session:
            orm = ORMUser(
                id=user.id,
                name=user.name,
                email=user.email.lower().strip(),
                username=user.username.lower().strip(),
                password_hash=user.password_hash,
                auth_provider=user.auth_provider,
                google_id=user.google_id,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_approved=user.is_approved,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)

    async def update(self, user: DomainUser) -> DomainUser:
        async with get_session() as session:
            orm = (
                await session.exec(select(ORMUser).where(ORMUser.id == user.id))
            ).first()
            if not orm:
                raise ValueError(f"User {user.id} not found")

            orm.name = user.name
            orm.is_active = user.is_active
            orm.is_approved = user.is_approved
            orm.role = user.role
            orm.avatar_url = user.avatar_url
            if user.password_hash:
                orm.password_hash = user.password_hash
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)
