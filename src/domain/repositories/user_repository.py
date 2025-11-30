from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.user import User

class AbstractUserRepository(ABC):
    """
    Abstract base class for User Repository.
    Defines the interface for interacting with user data storage.
    """

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by their unique ID.
        Args:
            user_id (int): The unique identifier of the user.
        Returns:
            Optional[User]: The User object if found, otherwise None.
        """
        raise NotImplementedError

    @abstractmethod
    async def add(self, user: User) -> None:
        """
        Adds a new user to the storage.
        Args:
            user (User): The User object to add.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> None:
        """
        Updates an existing user's information in the storage.
        Args:
            user (User): The User object with updated information.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """
        Deletes a user from the storage by their ID.
        Args:
            user_id (int): The unique identifier of the user to delete.
        """
        raise NotImplementedError
