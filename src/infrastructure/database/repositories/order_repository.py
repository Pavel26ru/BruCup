from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.order import Order as DomainOrder, OrderStatus
from src.domain.repositories.order_repository import AbstractOrderRepository
from src.infrastructure.database.models.order import Order as ORMOrder

class SQLAlchemyOrderRepository(AbstractOrderRepository):
    """
    SQLAlchemy implementation of the Order Repository.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Optional[DomainOrder]:
        stmt = select(ORMOrder).where(ORMOrder.id == order_id)
        orm_order = (await self.session.execute(stmt)).scalar_one_or_none()
        if orm_order:
            return DomainOrder(
                id=orm_order.id,
                user_id=orm_order.user_id,
                address=orm_order.address,
                product_name=orm_order.product_name,
                volume=orm_order.volume,
                quantity=orm_order.quantity,
                milk_name=orm_order.milk_name,
                syrup_name=orm_order.syrup_name,
                pickup_time=orm_order.pickup_time,
                total_price=orm_order.total_price,
                status=orm_order.status,
                is_completed=orm_order.is_completed,
                created_at=orm_order.created_at,
                updated_at=orm_order.updated_at
            )
        return None

    async def add(self, order: DomainOrder) -> None:
        orm_order = ORMOrder(
            user_id=order.user_id,
            address=order.address,
            product_name=order.product_name,
            volume=order.volume,
            quantity=order.quantity,
            milk_name=order.milk_name,
            syrup_name=order.syrup_name,
            pickup_time=order.pickup_time,
            total_price=order.total_price,
            status=order.status,
            is_completed=order.is_completed
        )
        self.session.add(orm_order)
        await self.session.flush() # Flush to get the new ID
        order.id = orm_order.id # Update the domain object with the new ID
        await self.session.commit()


    async def update(self, order: DomainOrder) -> None:
        orm_order = await self.session.get(ORMOrder, order.id)
        if orm_order:
            orm_order.user_id = order.user_id
            orm_order.address = order.address
            orm_order.product_name = order.product_name
            orm_order.volume = order.volume
            orm_order.quantity = order.quantity
            orm_order.milk_name = order.milk_name
            orm_order.syrup_name = order.syrup_name
            orm_order.pickup_time = order.pickup_time
            orm_order.total_price = order.total_price
            orm_order.status = order.status
            orm_order.is_completed = order.is_completed
            # updated_at is handled by TimestampMixin
            await self.session.commit()
        else:
            raise ValueError(f"Order with ID {order.id} not found for update.")

    async def get_active_orders(self) -> List[DomainOrder]:
        stmt = select(ORMOrder).where(
            ORMOrder.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]),
            ORMOrder.is_completed == False
        )
        result = await self.session.execute(stmt)
        orm_orders = result.scalars().all()
        return [
            DomainOrder(
                id=orm_order.id,
                user_id=orm_order.user_id,
                address=orm_order.address,
                product_name=orm_order.product_name,
                volume=orm_order.volume,
                quantity=orm_order.quantity,
                milk_name=orm_order.milk_name,
                syrup_name=orm_order.syrup_name,
                pickup_time=orm_order.pickup_time,
                total_price=orm_order.total_price,
                status=orm_order.status,
                is_completed=orm_order.is_completed,
                created_at=orm_order.created_at,
                updated_at=orm_order.updated_at
            )
            for orm_order in orm_orders
        ]
