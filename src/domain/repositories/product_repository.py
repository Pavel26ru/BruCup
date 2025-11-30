from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.product import Product

class AbstractProductRepository(ABC):
    """
    Abstract base class for Product Repository.
    Defines the interface for interacting with product data storage.
    """

    @abstractmethod
    async def get_all(self) -> List[Product]:
        """
        Retrieves all products from the storage.
        Returns:
            List[Product]: A list of all Product objects.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieves a product by its unique ID.
        Args:
            product_id (int): The unique identifier of the product.
        Returns:
            Optional[Product]: The Product object if found, otherwise None.
        """
        raise NotImplementedError
