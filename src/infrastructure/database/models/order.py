from sqlalchemy import BigInteger, String, Integer, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from src.domain.entities.order import OrderStatus

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    address: Mapped[str] = mapped_column(String(255))
    product_name: Mapped[str] = mapped_column(String(100))
    volume: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    
    milk_name: Mapped[str] = mapped_column(String(100), nullable=True)
    syrup_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    pickup_time: Mapped[str] = mapped_column(String(5)) # Storing as "HH:MM"
    total_price: Mapped[int] = mapped_column(Integer)

    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status='{self.status.value}')>"
