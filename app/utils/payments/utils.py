"""
Contains Utility Functions to assist with payment operations

@author Emmanuel Olowu
@link: https://github.com/zeddyemy
"""
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from ...extensions import db
from ...models.user import AppUser
from ...models.payment import Payment, Transaction
from ...enums.payments import PaymentStatus, TransactionType, PaymentType, PaymentGatewayName
from ..helpers.basics import generate_random_string
from ..helpers.money import quantize_amount

def get_payment_providers() -> list[str]:
    providers = []
    for name, member in PaymentGatewayName.__members__.items():
        providers.append(member.value)
    
    return providers


def safe_compare_amounts(amount1, amount2):
    """Compare two amounts with financial-grade precision."""
    
    # Convert to CurrencyDecimal if not already
    decimal1 = quantize_amount(amount1)
    decimal2 = quantize_amount(amount2)
    
    return decimal1 == decimal2


def record_payment_transaction(
    user: AppUser,
    amount: Decimal,
    payment_method: str,
    status: PaymentStatus = PaymentStatus.PENDING,
    narration: str = None,
    reference: str = None,
    payment_type: PaymentType = PaymentType.WALLET_TOP_UP,
    extra_meta: Optional[dict] = None) -> tuple[Payment, Transaction]:
    """
    Create payment and transaction records atomically.
    
    Args:
        user: User making the payment
        amount: Payment amount
        payment_method: Payment method/gateway used
        status: Initial payment status
        narration: Payment description
        reference: Payment provider's reference (if available)
        payment_type: Type of payment (wallet top-up, order, subscription)
        extra_meta: Additional metadata for the payment
    
    Returns:
        tuple: (Payment record, Transaction record)
    """
    
    try:
        payment_key = f"PAY_{reference}"
        transaction_key = f"TRX_{reference}"
        
        # Prepare meta_info
        meta_info = {
            "payment_type": str(payment_type),
            **(extra_meta or {})
        }

        # create payment record
        payment: Payment = Payment.create_payment_record(
            key = reference,
            amount = amount,
            payment_method=payment_method,
            status=str(status),
            app_user=user,
            narration=narration,
            meta_info=meta_info,
            commit=False # Don't commit yet
        )
        
        # create transaction record
        transaction: Transaction = Transaction.create_transaction(
            key = reference,
            amount = amount,
            transaction_type=TransactionType.PAYMENT,
            narration=narration or f"Payment via {payment_method}",
            status=str(status),
            app_user=user,
            meta_info=meta_info,
            commit=False # Don't commit yet
        )

        # commit to both records in db
        db.session.commit()

        return payment, transaction
    except Exception as e:
        db.session.rollback()
        raise e
