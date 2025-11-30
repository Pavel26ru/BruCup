import json
from typing import List, Dict, Optional
from src.domain.entities.option import Option
from src.domain.repositories.option_repository import AbstractOptionRepository

class InMemoryOptionRepository(AbstractOptionRepository):
    """
    In-memory implementation of the Option Repository that loads data from a JSON file.
    """
    def __init__(self, file_path: str):
        self._options: Dict[str, List[Option]] = {}
        self._load_data(file_path)

    def _load_data(self, file_path: str):
        """Loads option data from a JSON file into memory."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category, items in data.items():
                    self._options[category] = [Option.from_dict(item, category) for item in items]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading options data: {e}")
            self._options = {}

    async def get_all_by_category(self, category: str) -> List[Option]:
        """
        Retrieves all options for a given category from in-memory storage.
        """
        return self._options.get(category, [])

    async def get_by_id(self, option_id: int) -> Optional[Option]:
        """
        Retrieves an option by its unique ID from in-memory storage.
        """
        for category_options in self._options.values():
            for option in category_options:
                if option.id == option_id:
                    return option
        return None