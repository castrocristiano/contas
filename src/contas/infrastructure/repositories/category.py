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
            name=orm.name,
            category_type=CategoryType(orm.category_type),
            is_active=orm.is_active,
        )

    async def get_by_id(
        self, category_id: UUID, only_active: bool = True
    ) -> DomainCategory | None:
        async with get_session() as session:
            query = select(ORMCategory).where(ORMCategory.id == category_id)
            if only_active:
                query = query.where(ORMCategory.is_active == True)
            orm = (await session.exec(query)).first()
            return self._to_domain(orm) if orm else None

    async def get_by_name(self, name: str) -> DomainCategory | None:
        async with get_session() as session:
            orm = (
                await session.exec(select(ORMCategory).where(ORMCategory.name == name))
            ).first()
            return self._to_domain(orm) if orm else None

    async def list_all(
        self,
        only_active: bool = True,
        category_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DomainCategory]:
        async with get_session() as session:
            query = select(ORMCategory)
            if only_active:
                query = query.where(ORMCategory.is_active == True)
            if category_type:
                query = query.where(ORMCategory.category_type == category_type)
            query = query.order_by(ORMCategory.name.asc()).offset(offset).limit(limit)
            results = (await session.exec(query)).all()
            return [self._to_domain(c) for c in results]

    async def create(self, category: DomainCategory) -> DomainCategory:
        async with get_session() as session:
            orm = ORMCategory(
                id=category.id,
                name=category.name,
                category_type=category.category_type,
                is_active=category.is_active,
            )
            session.add(orm)
            await session.commit()
            await session.refresh(orm)
            return self._to_domain(orm)
