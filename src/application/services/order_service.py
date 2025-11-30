from typing import Dict, Any
from src.application.services.product_service import ProductService
from src.application.services.option_service import OptionService

class OrderService:
    """
    Service for calculating order details.
    """
    def __init__(self, product_service: ProductService, option_service: OptionService):
        self.product_service = product_service
        self.option_service = option_service

    async def calculate_total(self, order_data: Dict[str, Any]) -> int:
        """
        Calculates the total price of an order based on the selected items.

        Args:
            order_data (Dict[str, Any]): The order data stored in the FSM state.

        Returns:
            int: The total price of the order.
        """
        total_price = 0
        quantity = order_data.get("quantity", 1)

        # Get base product price
        product = await self.product_service.get_product_by_id(order_data.get("product_id"))
        if product:
            selected_volume = order_data.get("volume")
            for volume in product.volumes:
                if volume.volume == selected_volume:
                    total_price += volume.price
                    break
        
        # Add milk price
        milk_id = order_data.get("milk_id")
        if milk_id:
            milk = await self.option_service.get_option_by_id(milk_id)
            if milk:
                total_price += milk.price

        # Add syrup price
        syrup_id = order_data.get("syrup_id")
        if syrup_id:
            syrup = await self.option_service.get_option_by_id(syrup_id)
            if syrup:
                total_price += syrup.price
        
        return total_price * quantity
