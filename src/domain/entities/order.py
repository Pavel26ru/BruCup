from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Order:
    """
    Represents an order in the domain layer.
    """
    user_id: int
    address: str
    product_name: str
    volume: str
    quantity: int
    pickup_time: str
    total_price: int
    
    milk_name: str | None = None
    syrup_name: str | None = None
    
    id: int | None = None
    status: OrderStatus = OrderStatus.PENDING
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
