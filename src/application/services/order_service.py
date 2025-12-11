from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.product_service import ProductService
from src.application.services.option_service import OptionService
from src.domain.entities.order import Order as DomainOrder, OrderStatus
from src.domain.repositories.order_repository import AbstractOrderRepository
from src.infrastructure.database.repositories.order_repository import SQLAlchemyOrderRepository # Use SQLAlchemy repo

class OrderService:
    """
    Service for calculating order details and managing orders.
    """
    def __init__(self, session: AsyncSession, product_service: ProductService, option_service: OptionService):
        """
        Initializes the OrderService with an AsyncSession and other services.
        Args:
            session (AsyncSession): The SQLAlchemy async session.
            product_service (ProductService): Service for product-related operations.
            option_service (OptionService): Service for option-related operations.
        """
        self.session = session
        self.product_service = product_service
        self.option_service = option_service
        self.order_repository: AbstractOrderRepository = SQLAlchemyOrderRepository(session) # Create repo inside service

    async def calculate_total(self, order_data: Dict[str, Any]) -> int:
        """
        Calculates the total price of an order based on the selected items.
        """
        total_price = 0
        quantity = order_data.get("quantity", 1)

        product = await self.product_service.get_product_by_id(order_data.get("product_id"))
        if product:
            selected_volume = order_data.get("volume")
            for volume in product.volumes:
                if volume.volume == selected_volume:
                    total_price += volume.price
                    break
        
        milk_id = order_data.get("milk_id")
        if milk_id:
            milk = await self.option_service.get_option_by_id(milk_id)
            if milk:
                total_price += milk.price

        syrup_id = order_data.get("syrup_id")
        if syrup_id:
            syrup = await self.option_service.get_option_by_id(syrup_id)
            if syrup:
                total_price += syrup.price
        
        return total_price * quantity

    async def create_order(self, order_data: Dict[str, Any]) -> DomainOrder:
        """
        Creates and saves a new order to the database.
        """
        # Fetch names for summary
        product = await self.product_service.get_product_by_id(order_data.get("product_id"))
        milk = await self.option_service.get_option_by_id(order_data.get("milk_id")) if order_data.get("milk_id") else None
        syrup = await self.option_service.get_option_by_id(order_data.get("syrup_id")) if order_data.get("syrup_id") else None

        total_price = await self.calculate_total(order_data)

        new_order = DomainOrder(
            user_id=order_data["user_id"],
            address=order_data["address"],
            product_name=product.name if product else "Unknown Product",
            volume=order_data["volume"],
            quantity=order_data["quantity"],
            milk_name=milk.name if milk else None,
            syrup_name=syrup.name if syrup else None,
            pickup_time=order_data["pickup_time"],
            total_price=total_price,
        )
        await self.order_repository.add(new_order)
        return new_order

    async def get_active_orders(self) -> List[DomainOrder]:
        """
        Retrieves all active orders from the database.
        """
        return await self.order_repository.get_active_orders()

    async def get_order_by_id(self, order_id: int) -> Optional[DomainOrder]:
        """
        Retrieves an order by its ID.
        """
        return await self.order_repository.get_by_id(order_id)
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[DomainOrder]:
        """
        Updates the status of an order.
        """
        order = await self.order_repository.get_by_id(order_id)
        if order:
            order.status = new_status
            await self.order_repository.update(order)
            return order
        return None

    async def complete_order(self, order_id: int) -> Optional[DomainOrder]:
        """
        Marks an order as completed.
        """
        order = await self.order_repository.get_by_id(order_id)
        if order:
            order.status = OrderStatus.COMPLETED
            order.is_completed = True
            await self.order_repository.update(order)
            return order
        return None