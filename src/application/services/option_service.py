from typing import List, Optional
from src.domain.entities.option import Option
from src.domain.repositories.option_repository import AbstractOptionRepository

class OptionService:
    """
    Service layer for managing option-related business logic.
    """
    def __init__(self, option_repository: AbstractOptionRepository):
        self.option_repository = option_repository

    async def get_options_by_category(self, category: str) -> List[Option]:
        """
        Retrieves all options for a given category.
        Args:
            category (str): The category of options to retrieve.
        Returns:
            List[Option]: A list of options.
        """
        return await self.option_repository.get_all_by_category(category)

    async def get_option_by_id(self, option_id: int) -> Optional[Option]:
        """
        Retrieves an option by its ID.
        Args:
            option_id (int): The unique identifier of the option.
        Returns:
            Optional[Option]: The Option object if found, otherwise None.
        """
        return await self.option_repository.get_by_id(option_id)