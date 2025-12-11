from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User as DomainUser
from src.domain.repositories.user_repository import AbstractUserRepository
from src.infrastructure.database.models.user import User as ORMUser

class SQLAlchemyUserRepository(AbstractUserRepository):
    """
    SQLAlchemy implementation of the User Repository.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[DomainUser]:
        stmt = select(ORMUser).where(ORMUser.id == user_id)
        orm_user = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm_user:
            return DomainUser(
                id=orm_user.id,
                username=orm_user.username,
                first_name=orm_user.first_name,
                last_name=orm_user.last_name,
                is_admin=orm_user.is_admin,
                created_at=orm_user.created_at,
                updated_at=orm_user.updated_at
            )
        return None

    async def add(self, user: DomainUser) -> None:
        orm_user = ORMUser(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin
        )
        self.session.add(orm_user)
        await self.session.commit()

    async def update(self, user: DomainUser) -> None:
        orm_user = await self.session.get(ORMUser, user.id)
        if orm_user:
            orm_user.username = user.username
            orm_user.first_name = user.first_name
            orm_user.last_name = user.last_name
            orm_user.is_admin = user.is_admin
            # updated_at is handled by TimestampMixin
            await self.session.commit()
        else:
            raise ValueError(f"User with ID {user.id} not found for update.")

    async def delete(self, user_id: int) -> None:
        orm_user = await self.session.get(ORMUser, user_id)
        if orm_user:
            await self.session.delete(orm_user)
            await self.session.commit()

    async def get_all(self) -> list[DomainUser]:
        """
        Retrieves all users from the database.
        """
        stmt = select(ORMUser)
        result = await self.session.execute(stmt)
        orm_users = result.scalars().all()
        return [
            DomainUser(
                id=orm_user.id,
                username=orm_user.username,
                first_name=orm_user.first_name,
                last_name=orm_user.last_name,
                is_admin=orm_user.is_admin,
                created_at=orm_user.created_at,
                updated_at=orm_user.updated_at
            )
            for orm_user in orm_users
        ]