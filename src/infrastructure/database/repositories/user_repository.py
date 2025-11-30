from typing import Dict, Optional
from src.domain.entities.user import User
from src.domain.repositories.user_repository import AbstractUserRepository

class InMemoryUserRepository(AbstractUserRepository):
    """
    Temporary in-memory implementation of AbstractUserRepository for development/testing.
    This will be replaced by a proper MySQL implementation using an ORM like SQLAlchemy.
    """
    def __init__(self):
        self._users: Dict[int, User] = {} # Stores user_id -> User object

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by their unique ID from in-memory storage.
        """
        return self._users.get(user_id)

    async def add(self, user: User) -> None:
        """
        Adds a new user to in-memory storage.
        """
        if user.id in self._users:
            raise ValueError(f"User with ID {user.id} already exists.")
        self._users[user.id] = user

    async def update(self, user: User) -> None:
        """
        Updates an existing user's information in in-memory storage.
        """
        if user.id not in self._users:
            raise ValueError(f"User with ID {user.id} does not exist.")
        self._users[user.id] = user

    async def delete(self, user_id: int) -> None:
        """
        Deletes a user from in-memory storage by their ID.
        """
        if user_id in self._users:
            del self._users[user_id]
