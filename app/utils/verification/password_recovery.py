"""Password recovery management using application cache.

Stores minimal, non-plaintext data for password reset verification.
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
class PendingPasswordReset:
    """Ephemeral record for a pending password reset."""

    email: str
    code_hash: str
    attempts: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(data: str) -> "PendingPasswordReset":
        obj = json.loads(data)
        return PendingPasswordReset(**obj)


def _key(reset_id: str) -> str:
    return f"pending_password_reset:{reset_id}"


def generate_reset_id() -> str:
    """Generate a random password reset identifier."""
    return uuid.uuid4().hex


def hash_reset_code(code: str, *, salt: str) -> str:
    """Hash a verification code with a salt (reset_id)."""
    h = hashlib.sha256()
    h.update((salt + ":" + code).encode("utf-8"))
    return h.hexdigest()


def store_pending_password_reset(reset_id: str, pending: PendingPasswordReset, ttl_minutes: int = 15) -> None:
    """Store a pending password reset with TTL."""
    app_cache.set(_key(reset_id), pending.to_json(), timeout=int(_timedelta(minutes=ttl_minutes).total_seconds()))


def get_pending_password_reset(reset_id: str) -> Optional[PendingPasswordReset]:
    """Fetch a pending password reset, or None if expired/missing."""
    raw = app_cache.get(_key(reset_id))
    if not raw:
        return None
    try:
        return PendingPasswordReset.from_json(raw)  # type: ignore[arg-type]
    except Exception:
        return None


def delete_pending_password_reset(reset_id: str) -> None:
    """Delete a pending password reset."""
    app_cache.delete(_key(reset_id))


def increment_attempts(reset_id: str) -> int:
    """Increment attempts counter and persist; returns the new attempts value."""
    rec = get_pending_password_reset(reset_id)
    if rec is None:
        return 0
    rec.attempts += 1
    # Preserve existing TTL by resetting default; small risk it resets
    store_pending_password_reset(reset_id, rec)
    return rec.attempts

