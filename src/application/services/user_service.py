from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User as DomainUser
from src.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository # Use SQLAlchemy repo

class UserService:
    """
    Service layer for managing user-related business logic.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the UserService with an AsyncSession.
        Args:
            session (AsyncSession): The SQLAlchemy async session.
        """
        self.user_repository = SQLAlchemyUserRepository(session) # Create repo inside service

    async def get_or_create_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None
    ) -> DomainUser:
        """
        Retrieves an existing user or creates a new one if they don't exist.
        Handles race conditions where two calls might try to create the same user.
        """
        user = await self.user_repository.get_by_id(user_id)
        if user:
            # Update user info if it changed
            if (user.username != username or
                    user.first_name != first_name or
                    user.last_name != last_name):
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.updated_at = datetime.now()
                await self.user_repository.update(user)
            return user
        else:
            new_user = DomainUser(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            try:
                await self.user_repository.add(new_user)
                return new_user
            except IntegrityError:
                # This handles a race condition: if another process created the user
                # between our initial check and our 'add' call, the 'add' will fail.
                # We need to rollback the session to clear the failed transaction.
                await self.user_repository.session.rollback()
                # In this case, we just fetch the user that was created.
                return await self.user_repository.get_by_id(user_id)

    async def get_user_by_id(self, user_id: int) -> DomainUser | None:
        """
        Retrieves a user by their ID.
        """
        return await self.user_repository.get_by_id(user_id)

    async def update_user(self, user: DomainUser) -> None:
        """
        Updates an existing user.
        """
        user.updated_at = datetime.now()
        await self.user_repository.update(user)

    async def get_all_users(self) -> list[DomainUser]:
        """
        Retrieves all users.
        """
        return await self.user_repository.get_all()