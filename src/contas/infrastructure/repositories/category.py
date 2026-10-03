from uuid import UUID

from sqlmodel import select

from contas.application.ports.repositories import ICategoryRepository
from contas.db.session import get_session
from contas.domain.entities import Category as DomainCategory
from contas.domain.enums import CategoryType
from contas.models.category import Category as ORMCategory


class SQLAlchemyCategoryRepository(ICategoryRepository):
    def _to_domain(self, orm: ORMCategory) -> DomainCategory:
        return DomainCategory(
            id=orm.id,
            user_id=orm.user_id,
            name=orm.name,
            category_type=CategoryType(orm.category_type),
            is_active=orm.is_active,
        )

    async def get_by_id(
        self, category_id: UUID, user_id: UUID | None = None, only_active: bool = True
    ) -> DomainCategory | None:
        async with get_session() as session:
            query = select(ORMCategory).where(ORMCategory.id == category_id)
            if user_id:
                query = query.where(ORMCategory.user_id == user_id)
            if only_active:
                query = query.where(ORMCategory.is_active == True)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def get_by_name(
        self, name: str, user_id: UUID | None = None
    ) -> DomainCategory | None:
        async with get_session() as session:
            query = select(ORMCategory).where(ORMCategory.name == name)
            if user_id:
                query = query.where(ORMCategory.user_id == user_id)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def list_all(
        self,
        user_id: UUID | None = None,
        only_active: bool = True,
        category_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DomainCategory]:
        async with get_session() as session:
            query = select(ORMCategory)
            if user_id:
                query = query.where(ORMCategory.user_id == user_id)
            if only_active:
                query = query.where(ORMCategory.is_active == True)
            if category_type:
                query = query.where(ORMCategory.category_type == category_type)
            query = query.order_by(ORMCategory.name.asc()).offset(offset).limit(limit)
            results = (await session.exec(query)).all()
            return [self._to_domain(c) for c in results]

    async def create(self, category: DomainCategory) -> DomainCategory:
        async with get_session() as session:
            effective_user_id = category.user_id
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

            orm = ORMCategory(
                id=category.id,
                user_id=effective_user_id,
                name=category.name,
                category_type=category.category_type,
                is_active=category.is_active,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)
