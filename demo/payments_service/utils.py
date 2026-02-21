"""Utility module for demo payments service.

Shared utilities used across API, worker, repository, and notification layers.
Changes here have wide blast radius.
"""

import hashlib
import time
import uuid
from typing import Callable, TypeVar

from demo.payments_service.config import PaymentConfig, load_config

T = TypeVar("T")


def format_amount(amount: float) -> str:
    """Format numeric amount for display.

    Args:
        amount: Monetary amount.

    Returns:
        str: Formatted amount string.
    """
    return f"${amount:.2f}"


def generate_payment_id() -> str:
    """Generate a unique payment identifier.

    Returns:
        str: UUID-based payment id.
    """
    return f"pay_{uuid.uuid4().hex[:16]}"


def generate_transaction_id() -> str:
    """Generate a unique transaction identifier.

    Returns:
        str: UUID-based transaction id.
    """
    return f"txn_{uuid.uuid4().hex[:16]}"


def compute_audit_hash(payment_id: str, amount: float, currency: str) -> str:
    """Compute integrity hash for audit trail.

    Args:
        payment_id: Payment identifier.
        amount: Payment amount.
        currency: Currency code.

    Returns:
        str: SHA-256 hex digest.
    """
    data = f"{payment_id}:{amount}:{currency}"
    return hashlib.sha256(data.encode()).hexdigest()


def retry_with_backoff(
    func: Callable[[], T],
    config: PaymentConfig | None = None,
) -> T:
    """Execute function with retry and exponential backoff.

    Args:
        func: Callable to execute.
        config: Configuration for retry limits.

    Returns:
        T: Function result on success.

    Raises:
        Exception: Last exception after all retries exhausted.
    """
    cfg = config or load_config()
    last_error: Exception | None = None
    for attempt in range(cfg.retry_max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            time.sleep(cfg.retry_backoff_seconds * (2 ** attempt))
    raise last_error  # type: ignore[misc]


def mask_email(email: str) -> str:
    """Mask an email address for logging (privacy).

    Args:
        email: Full email address.

    Returns:
        str: Masked email string.
    """
    if "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    masked_local = local[0] + "***" if local else "***"
    return f"{masked_local}@{domain}"
