"""
Money and currency utilities.

Provides helpers for Decimal quantization and basic currency formatting used in
payments and wallet operations.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union


TAmount = Union[int, float, Decimal, str]


def quantize_amount(amount: TAmount, places: str = "0.01") -> Decimal:
    """
    Quantize an amount to two decimal places using bankers' rounding.

    Args:
        amount: The numeric amount to quantize
        places: Decimal quantization pattern, default 2dp

    Returns:
        Decimal: Quantized amount
    """
    try:
        dec = Decimal(str(amount))
        return dec.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid amount: {amount}") from exc


def format_currency(amount: TAmount, symbol: str = "₦") -> str:
    """Format amount with thousands separator and currency symbol."""
    quantized = quantize_amount(amount)
    return f"{symbol}{quantized:,.2f}"


def format_price(amount: TAmount) -> str:
    """Alias for format_currency for backward compatibility."""
    return format_currency(amount)

