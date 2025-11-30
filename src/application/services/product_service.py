from typing import List, Optional
from src.domain.entities.product import Product
from src.domain.repositories.product_repository import AbstractProductRepository

class ProductService:
    """
    Service layer for managing product-related business logic.
    """
    def __init__(self, product_repository: AbstractProductRepository):
        """
        Initializes the ProductService with an AbstractProductRepository.
        Args:
            product_repository (AbstractProductRepository): An implementation of the product repository interface.
        """
        self.product_repository = product_repository

    async def get_all_products(self) -> List[Product]:
        """
        Retrieves all products.
        Returns:
            List[Product]: A list of all products.
        """
        return await self.product_repository.get_all()

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieves a product by its ID.
        Args:
            product_id (int): The unique identifier of the product.
        Returns:
            Optional[Product]: The Product object if found, otherwise None.
        """
        return await self.product_repository.get_by_id(product_id)
