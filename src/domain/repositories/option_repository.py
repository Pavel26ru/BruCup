from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.option import Option

class AbstractOptionRepository(ABC):
    """
    Abstract base class for Option Repository.
    """

    @abstractmethod
    async def get_all_by_category(self, category: str) -> List[Option]:
        """
        Retrieves all options for a given category.
        Args:
            category (str): The category of options to retrieve (e.g., "milk", "syrup").
        Returns:
            List[Option]: A list of all Option objects for the category.
        """
    @abstractmethod
    async def get_by_id(self, option_id: int) -> Optional[Option]:
        """
        Retrieves an option by its unique ID.
        Args:
            option_id (int): The unique identifier of the option.
        Returns:
            Optional[Option]: The Option object if found, otherwise None.
        """
        raise NotImplementedError
