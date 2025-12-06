from enum import Enum

class OrderStatus(Enum):
    """
    Enumeration of possible order statuses.
    """
    PENDING = "pending"
    PENDING_PAYMENT = "pending_payment"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"

    def __str__(self):
        return self.value