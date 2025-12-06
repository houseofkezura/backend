from enum import Enum


class PaymentMethods(Enum):
    """
    Enum representing available payment methods.
    """
    BACS = "bacs"
    CHECK = "check"
    COD = "cod"
    GATEWAY = "gateway"
    WALLET = "wallet"

    def __str__(self):
        return self.value  # Returns "bacs", "check", etc.

class TransferStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class PaymentStatus(Enum):
    """ENUMS for the payment status field in Payment Model"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    REVERSED = "reversed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"
    
    def __str__(self) -> str:
        return self.value  # Ensures usage as strings in queries
    

class PaymentType(Enum):
    """
    Types of payments supported in the application.
    """
    WALLET_TOP_UP = "wallet_top_up"
    ESIM_PURCHASE = "esim_purchase"
    ORDER_PAYMENT = "order_payment"
    SUBSCRIPTION = "subscription"
    
    def __str__(self) -> str:
        return self.value

class TransactionType(Enum):
    """ENUMS for the transaction_type field in Transaction Model"""
    CREDIT = "credit"
    DEBIT = "debit"
    PAYMENT = "payment"
    WITHDRAWAL = "withdrawal"
    
    def __str__(self) -> str:
        return self.value  # Ensures usage as strings in queries

class PaymentGatewayName(Enum):
    """ENUMS for the payment gateway"""
    BITPAY = "BitPay"
    FLUTTERWAVE = "Flutterwave"
    PAYSTACK = "Paystack"
    # COINBASE = "CoinBase"
    # STRIP = "Stripe"
    
    def __str__(self) -> str:
        return self.value  # Returns "BitPay", "CoinBase", etc.