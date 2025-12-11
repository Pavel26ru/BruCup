from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.order import Order

class AbstractOrderRepository(ABC):
    """
    Abstract base class for Order Repository.
    """

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Retrieves an order by its unique ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def add(self, order: Order) -> None:
        """
        Adds a new order to the storage.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, order: Order) -> None:
        """
        Updates an existing order's information in the storage.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active_orders(self) -> List[Order]:
        """
        Retrieves all active (not completed or cancelled) orders.
        """
        raise NotImplementedError
