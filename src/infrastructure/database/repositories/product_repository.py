import json
from typing import List, Optional, Dict
from src.domain.entities.product import Product
from src.domain.repositories.product_repository import AbstractProductRepository

class InMemoryProductRepository(AbstractProductRepository):
    """
    In-memory implementation of the Product Repository that loads data from a JSON file.
    This is suitable for menus that do not change often.
    """
    def __init__(self, file_path: str):
        """
        Initializes the repository and loads the menu from the specified JSON file.
        Args:
            file_path (str): The path to the menu.json file.
        """
        self._products: Dict[int, Product] = {}
        self._load_data(file_path)

    def _load_data(self, file_path: str):
        """Loads product data from a JSON file into memory."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    product = Product.from_dict(item)
                    self._products[product.id] = product
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # In a real application, you'd want better error handling/logging
            print(f"Error loading menu data: {e}")
            self._products = {}

    async def get_all(self) -> List[Product]:
        """
        Retrieves all products from in-memory storage.
        """
        return list(self._products.values())

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieves a product by its unique ID from in-memory storage.
        """
        return self._products.get(product_id)

