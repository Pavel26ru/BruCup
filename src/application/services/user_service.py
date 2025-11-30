from src.domain.entities.user import User
from src.domain.repositories.user_repository import AbstractUserRepository
from datetime import datetime

class UserService:
    """
    Service layer for managing user-related business logic.
    Interacts with the AbstractUserRepository to perform CRUD operations on User entities.
    """

    def __init__(self, user_repository: AbstractUserRepository):
        """
        Initializes the UserService with an AbstractUserRepository.
        Args:
            user_repository (AbstractUserRepository): An implementation of the user repository interface.
        """
        self.user_repository = user_repository

    async def get_or_create_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None
    ) -> User:
        """
        Retrieves an existing user or creates a new one if they don't exist.
        Args:
            user_id (int): Telegram user ID.
            username (str | None): Telegram username.
            first_name (str): Telegram first name.
            last_name (str | None): Telegram last name.
        Returns:
            User: The retrieved or newly created User object.
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
            new_user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            await self.user_repository.add(new_user)
            return new_user

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their ID.
        Args:
            user_id (int): The unique identifier of the user.
        Returns:
            User | None: The User object if found, otherwise None.
        """
        return await self.user_repository.get_by_id(user_id)

    async def update_user(self, user: User) -> None:
        """
        Updates an existing user.
        Args:
            user (User): The User object with updated information.
        """
        user.updated_at = datetime.now()
        await self.user_repository.update(user)
