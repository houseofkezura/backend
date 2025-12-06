"""
Currency conversion utility for converting USD to NGN.

Fetches live exchange rates from exchangerate-api.com, caches for 24 hours,
and provides fallback mechanisms for reliability.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import requests

from ...extensions import app_cache
from config import Config
from ...logging import log_error, log_event


class CurrencyConverter:
    """
    Currency converter for USD to NGN conversion.
    
    Features:
    - Fetches live rates from exchangerate-api.com
    - Caches rates for 24 hours
    - Fallback to stale cache on API failure
    - Optional markup percentage for margin protection
    - Hardcoded fallback rate if all else fails
    """
    
    # Hardcoded fallback rate (updated periodically)
    FALLBACK_RATE = Decimal("1500.00")
    
    # Cache key for exchange rate
    CACHE_KEY = "usd_ngn_exchange_rate"
    CACHE_KEY_TIMESTAMP = "usd_ngn_exchange_rate_timestamp"
    
    # Cache TTL: 24 hours
    CACHE_TTL_SECONDS = 24 * 60 * 60
    
    # Stale cache threshold: 48 hours (use stale cache if less than 48h old)
    STALE_CACHE_THRESHOLD_SECONDS = 48 * 60 * 60
    
    def __init__(self, markup_percentage: Optional[float] = None):
        """
        Initialize currency converter.
        
        Args:
            markup_percentage: Optional markup percentage (e.g., 3.0 for 3% markup)
        """
        self.markup_percentage = markup_percentage or getattr(Config, 'CURRENCY_MARKUP_PERCENTAGE', 0.0)
        self.api_key = Config.EXCHANGE_RATE_API_KEY
        self.api_url = Config.EXCHANGE_RATE_API_URL
    
    def get_rate(self, use_stale_cache: bool = True) -> Decimal:
        """
        Get USD to NGN exchange rate.
        
        Tries in order:
        1. Fresh cached rate (< 24 hours)
        2. API fetch (if cache expired)
        3. Stale cached rate (< 48 hours, if use_stale_cache=True)
        4. Hardcoded fallback rate
        
        Args:
            use_stale_cache: Whether to use stale cache as fallback
            
        Returns:
            Exchange rate as Decimal
        """
        # Try fresh cache first
        cached_rate = self._get_cached_rate()
        if cached_rate and self._is_cache_fresh():
            log_event("Using fresh cached exchange rate", {"rate": str(cached_rate)})
            return self._apply_markup(cached_rate)
        
        # Try fetching from API
        try:
            fresh_rate = self._fetch_rate_from_api()
            if fresh_rate:
                self._cache_rate(fresh_rate)
                log_event("Fetched fresh exchange rate from API", {"rate": str(fresh_rate)})
                return self._apply_markup(fresh_rate)
        except Exception as e:
            log_error("Failed to fetch exchange rate from API", error=e)
        
        # Fallback to stale cache if allowed
        if use_stale_cache and cached_rate and self._is_cache_stale_but_usable():
            log_event("Using stale cached exchange rate", {"rate": str(cached_rate)})
            return self._apply_markup(cached_rate)
        
        # Final fallback to hardcoded rate
        log_event("Using fallback exchange rate", {"rate": str(self.FALLBACK_RATE)})
        return self._apply_markup(self.FALLBACK_RATE)
    
    def convert_usd_to_ngn(self, usd_amount: Decimal, rate: Optional[Decimal] = None) -> Decimal:
        """
        Convert USD amount to NGN.
        
        Args:
            usd_amount: Amount in USD
            rate: Optional exchange rate (if None, fetches current rate)
            
        Returns:
            Amount in NGN (rounded to 2 decimal places)
        """
        if rate is None:
            rate = self.get_rate()
        
        ngn_amount = usd_amount * rate
        return ngn_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_rate_metadata(self) -> Dict[str, Any]:
        """
        Get exchange rate with metadata.
        
        Returns:
            Dictionary with rate, source, timestamp, and markup info
        """
        cached_rate = self._get_cached_rate()
        cached_timestamp = self._get_cached_timestamp()
        
        # Determine source
        if cached_rate and self._is_cache_fresh():
            source = "cache_fresh"
        elif cached_rate and self._is_cache_stale_but_usable():
            source = "cache_stale"
        else:
            # Try API
            try:
                fresh_rate = self._fetch_rate_from_api()
                if fresh_rate:
                    self._cache_rate(fresh_rate)
                    source = "api"
                    cached_rate = fresh_rate
                    cached_timestamp = datetime.utcnow().isoformat()
                else:
                    source = "fallback"
                    cached_rate = self.FALLBACK_RATE
                    cached_timestamp = None
            except Exception:
                source = "fallback"
                cached_rate = self.FALLBACK_RATE
                cached_timestamp = None
        
        rate = self._apply_markup(cached_rate) if cached_rate else self._apply_markup(self.FALLBACK_RATE)
        
        return {
            "rate": float(rate),
            "base_rate": float(cached_rate) if cached_rate else float(self.FALLBACK_RATE),
            "source": source,
            "timestamp": cached_timestamp,
            "markup_percentage": self.markup_percentage,
            "currency_pair": "USD/NGN"
        }
    
    def _fetch_rate_from_api(self) -> Optional[Decimal]:
        """
        Fetch exchange rate from exchangerate-api.com.
        
        Returns:
            Exchange rate as Decimal or None if fetch fails
        """
        if not self.api_key:
            log_error("Exchange rate API key not configured")
            return None
        
        try:
            # exchangerate-api.com v6 format: /latest/USD
            response = requests.get(
                f"{self.api_url}/USD",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract NGN rate
            rates = data.get('conversion_rates', {})
            ngn_rate = rates.get('NGN')
            
            if ngn_rate:
                return Decimal(str(ngn_rate))
            else:
                log_error("NGN rate not found in API response")
                return None
                
        except requests.exceptions.RequestException as e:
            log_error("Failed to fetch exchange rate from API", error=e)
            return None
        except (ValueError, KeyError) as e:
            log_error("Invalid exchange rate API response", error=e)
            return None
    
    def _get_cached_rate(self) -> Optional[Decimal]:
        """Get cached exchange rate."""
        cached = app_cache.get(self.CACHE_KEY)
        return Decimal(str(cached)) if cached else None
    
    def _get_cached_timestamp(self) -> Optional[str]:
        """Get cached rate timestamp."""
        return app_cache.get(self.CACHE_KEY_TIMESTAMP)
    
    def _is_cache_fresh(self) -> bool:
        """Check if cached rate is fresh (< 24 hours)."""
        timestamp_str = self._get_cached_timestamp()
        if not timestamp_str:
            return False
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = (datetime.utcnow() - timestamp).total_seconds()
            return age < self.CACHE_TTL_SECONDS
        except (ValueError, TypeError):
            return False
    
    def _is_cache_stale_but_usable(self) -> bool:
        """Check if cached rate is stale but still usable (< 48 hours)."""
        timestamp_str = self._get_cached_timestamp()
        if not timestamp_str:
            return False
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = (datetime.utcnow() - timestamp).total_seconds()
            return age < self.STALE_CACHE_THRESHOLD_SECONDS
        except (ValueError, TypeError):
            return False
    
    def _cache_rate(self, rate: Decimal) -> None:
        """Cache exchange rate with timestamp."""
        timestamp = datetime.utcnow().isoformat()
        app_cache.set(self.CACHE_KEY, str(rate), timeout=self.CACHE_TTL_SECONDS)
        app_cache.set(self.CACHE_KEY_TIMESTAMP, timestamp, timeout=self.CACHE_TTL_SECONDS)
    
    def _apply_markup(self, rate: Decimal) -> Decimal:
        """Apply markup percentage to rate."""
        if self.markup_percentage <= 0:
            return rate
        
        markup_multiplier = Decimal('1') + (Decimal(str(self.markup_percentage)) / Decimal('100'))
        return (rate * markup_multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# Singleton instance
_currency_converter: Optional[CurrencyConverter] = None


def get_currency_converter() -> CurrencyConverter:
    """
    Get singleton CurrencyConverter instance.
    
    Returns:
        CurrencyConverter instance
    """
    global _currency_converter
    if _currency_converter is None:
        _currency_converter = CurrencyConverter()
    return _currency_converter

