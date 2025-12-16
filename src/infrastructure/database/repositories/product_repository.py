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
        self._categories: Dict[str, List[Product]] = {} # New: store products by category
        self._load_data(file_path)

    def _load_data(self, file_path: str):
        """Loads product data from a JSON file into memory, handling categories."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category_item in data:
                    # Each category_item is a dict like {"CategoryName": [product_list]}
                    for category_name, products_list in category_item.items():
                        self._categories[category_name] = [] # Initialize list for the category
                        for item_data in products_list:
                            product = Product.from_dict(item_data)
                            self._products[product.id] = product
                            self._categories[category_name].append(product)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading menu data: {e}")
            self._products = {}
            self._categories = {}

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

    async def get_categories(self) -> List[str]:
        """
        Retrieves all product category names.
        """
        return list(self._categories.keys())

    async def get_products_by_category(self, category_name: str) -> List[Product]:
        """
        Retrieves all products within a specific category.
        """
        return self._categories.get(category_name, [])

