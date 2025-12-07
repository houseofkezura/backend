"""Pending registration management using application cache.

Stores minimal, non-plaintext data for signup verification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta as _timedelta
import hashlib
import json
import uuid
from typing import Optional

from app.extensions import app_cache


@dataclass
class PendingRegistration:
    """Ephemeral record for a pending user signup."""

    email: str
    firstname: str
    lastname: str
    username: Optional[str]
    password_hash: str
    code_hash: str
    password: Optional[str] = None  # Temporary plain password for Clerk user creation (cleared after use)
    attempts: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(data: str) -> "PendingRegistration":
        obj = json.loads(data)
        return PendingRegistration(**obj)


def _key(reg_id: str) -> str:
    return f"pending_registration:{reg_id}"


def generate_registration_id() -> str:
    """Generate a random registration identifier."""
    return uuid.uuid4().hex


def hash_code(code: str, *, salt: str) -> str:
    """Hash a verification code with a salt (reg_id)."""
    h = hashlib.sha256()
    h.update((salt + ":" + code).encode("utf-8"))
    return h.hexdigest()


def store_pending_registration(reg_id: str, pending: PendingRegistration, ttl_minutes: int = 15) -> None:
    """Store a pending registration with TTL."""
    app_cache.set(_key(reg_id), pending.to_json(), timeout=int(_timedelta(minutes=ttl_minutes).total_seconds()))


def get_pending_registration(reg_id: str) -> Optional[PendingRegistration]:
    """Fetch a pending registration, or None if expired/missing."""
    raw = app_cache.get(_key(reg_id))
    if not raw:
        return None
    try:
        return PendingRegistration.from_json(raw)  # type: ignore[arg-type]
    except Exception:
        return None


def delete_pending_registration(reg_id: str) -> None:
    app_cache.delete(_key(reg_id))


def increment_attempts(reg_id: str) -> int:
    """Increment attempts counter and persist; returns the new attempts value."""
    rec = get_pending_registration(reg_id)
    if rec is None:
        return 0
    rec.attempts += 1
    # Preserve existing TTL by resetting default; small risk it resets
    store_pending_registration(reg_id, rec)
    return rec.attempts


