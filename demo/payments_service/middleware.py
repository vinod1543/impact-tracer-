"""Middleware layer for payment API.

Cross-cutting concerns: authentication, rate limiting, request logging.
These wrap around the API handlers and affect every incoming request.
"""

from __future__ import annotations

import time
from typing import Callable

from demo.payments_service.config import PaymentConfig, load_config
from demo.payments_service.utils import mask_email


class AuthMiddleware:
    """Validates API authentication tokens.

    All API endpoints pass through this middleware before processing.
    """

    VALID_API_KEYS = {"test-key-001", "prod-key-002", "merchant-key-003"}

    def authenticate(self, api_key: str) -> bool:
        """Verify an API key is valid.

        Args:
            api_key: Client-provided API key.

        Returns:
            bool: True if key is valid.
        """
        return api_key in self.VALID_API_KEYS

    def extract_merchant_from_key(self, api_key: str) -> str:
        """Derive merchant identifier from API key.

        Args:
            api_key: Authenticated API key.

        Returns:
            str: Merchant identifier.
        """
        return f"merchant_{api_key.split('-')[0]}"


class RateLimiter:
    """Simple in-memory rate limiter.

    Protects API endpoints from abuse. Used by the API layer.
    """

    def __init__(self, max_requests_per_minute: int = 60) -> None:
        self.max_rpm = max_requests_per_minute
        self._window: dict[str, list[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if a client is within rate limits.

        Args:
            client_id: Client/merchant identifier.

        Returns:
            bool: True if request is allowed.
        """
        now = time.time()
        window = self._window.setdefault(client_id, [])
        # Prune old entries
        window[:] = [t for t in window if now - t < 60]
        if len(window) >= self.max_rpm:
            return False
        window.append(now)
        return True


class RequestLogger:
    """Logs incoming API requests with privacy masking.

    Uses utils.mask_email to sanitize PII before logging.
    """

    def __init__(self) -> None:
        self._logs: list[dict] = []

    def log_request(self, endpoint: str, merchant_id: str, customer_email: str = "") -> None:
        """Log an incoming request.

        Args:
            endpoint: API endpoint path.
            merchant_id: Merchant identifier.
            customer_email: Customer email (will be masked).
        """
        entry = {
            "endpoint": endpoint,
            "merchant_id": merchant_id,
            "customer_email": mask_email(customer_email) if customer_email else "",
            "timestamp": time.time(),
        }
        self._logs.append(entry)

    def get_recent_logs(self, count: int = 10) -> list[dict]:
        """Return most recent log entries.

        Args:
            count: Number of entries to return.

        Returns:
            list[dict]: Recent log entries.
        """
        return self._logs[-count:]
