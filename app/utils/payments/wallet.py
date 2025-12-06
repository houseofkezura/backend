'''
This module defines helper functions to carry out user wallet operations.

These functions assist with operations such as:
    * crediting wallet
    * debiting wallet
    * fetching wallet balance. e.t.c...

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy
'''
from decimal import Decimal

from ...extensions import db
from ...logging import log_event, log_error
from ...models import Wallet, AppUser
from ..date_time import DateTimeUtils
from ..helpers.basics import generate_random_string
from ..helpers.api_response import error_response, success_response
from ..helpers.money import quantize_amount

from config import Config



def debit_wallet(user_id: int, amount: int, payment_type=None, commit: bool = True) -> Decimal:
    """
    Debit the user's wallet.

    Args:
        user_id (int): ID of the user
        amount (int): Amount to debit

    Returns:
        Decimal: Updated wallet balance
    """
    user: AppUser = AppUser.query.get(user_id)
    
    if user is None:
        raise ValueError("User not found.")
    
    wallet: Wallet = user.wallet

    if wallet is None:
        raise ValueError("User does not have a wallet.")

    current_balance = wallet.balance
    amount =  Decimal(amount)
    amount = quantize_amount(amount)
    
    log_event('current_balance', current_balance)
    
    if current_balance < amount:
        raise ValueError("Insufficient balance.")

    
    try:
        # Debit the wallet
        wallet.balance -= amount
        key = generate_random_string(16)
        
        if commit:
            db.session.commit()
        log_event('current_balance', wallet.balance)
        return wallet.balance
    except Exception as e:
        # Handle the exception appropriately (rollback, log the error, etc.)
        db.session.rollback()
        raise e


def credit_wallet(user_id: int, amount: int | float | Decimal, commit: bool = True) -> Decimal:
    """
    Credit the user's wallet.

    Args:
        user_id (int): ID of the user
        amount (int | float | Decimal): Amount to credit

    Returns:
        Decimal: Updated wallet balance
    """
    user: AppUser = AppUser.query.get(user_id)
    
    if user is None:
        raise ValueError("User not found.")
    
    wallet: Wallet = user.wallet

    if wallet is None:
        raise ValueError("User does not have a wallet.")
    
    amount =  Decimal(amount)
    amount = quantize_amount(amount)


    try:
        # Credit the wallet
        wallet.balance += amount
        if commit:
            db.session.commit()
        return wallet.balance
    except Exception as e:
        # Handle the exception appropriately (rollback, log the error, etc.)
        db.session.rollback()
        raise e


def refund_to_wallet(user_id: int, amount: int | float | Decimal, commit: bool = True) -> Decimal:
    """
    This function processes a refund for a user with a 1.5% fee deduction.

    Args:
        user_id: The ID of the user to be refunded.
        amount: The original amount paid.

    Returns:
        wallet ballance if the refund was successful, raises exception otherwise.
    """
    user: AppUser = AppUser.query.get(user_id)
    
    if user is None:
        raise ValueError("User not found.")
    
    wallet: Wallet = user.wallet

    if wallet is None:
        raise ValueError("User does not have a wallet.")
    
    amount = quantize_amount(amount)
    
    fee_percentage = Decimal('0.015')  # Represents 1.5% as a decimal
    fee = amount * fee_percentage
    refund_amount = amount - fee
    
    try:
        # Credit the wallet
        wallet.balance += Decimal(refund_amount)
        if commit:
            db.session.commit()
        
        return wallet.balance
    except Exception as e:
        # Handle the exception appropriately (rollback, log the error, etc.)
        db.session.rollback()
        raise e

