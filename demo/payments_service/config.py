"""Service configuration and feature flags.

Centralizes configuration that controls behavior across modules.
Changes here propagate to API, worker, validator, and notification layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PaymentConfig:
    """Global payment service configuration.

    Attributes:
        max_payment_amount: Maximum allowed single payment.
        min_payment_amount: Minimum allowed single payment.
        supported_currencies: List of accepted currency codes.
        risk_threshold: Score above which payments are flagged.
        retry_max_attempts: Max retry attempts for failed operations.
        retry_backoff_seconds: Base backoff between retries.
        enable_notifications: Feature flag for email notifications.
        enable_fraud_check: Feature flag for fraud screening.
        idempotency_ttl_seconds: TTL for idempotency key cache.
    """

    max_payment_amount: float = 50000.00
    min_payment_amount: float = 0.50
    supported_currencies: list = field(default_factory=lambda: ["USD", "EUR", "GBP"])
    risk_threshold: float = 0.75
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 1.0
    enable_notifications: bool = True
    enable_fraud_check: bool = True
    idempotency_ttl_seconds: int = 86400


def load_config() -> PaymentConfig:
    """Load payment configuration from environment / defaults.

    Returns:
        PaymentConfig: Loaded configuration instance.
    """
    return PaymentConfig()


def get_supported_currencies(config: PaymentConfig) -> list:
    """Return list of supported currencies from config.

    Args:
        config: Payment configuration.

    Returns:
        list: Supported currency codes.
    """
    return list(config.supported_currencies)
