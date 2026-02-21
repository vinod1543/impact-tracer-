"""API module for demo payments service."""

from demo.payments_service.validator import BasePaymentValidator
from demo.payments_service.utils import format_amount


def process_payment(payload: dict) -> bool:
    """Process payment payload via validator.

    Args:
        payload: Payment payload.

    Returns:
        bool: Validation status.
    """
    _ = format_amount(float(payload.get("amount", 0)))
    validator = BasePaymentValidator()
    return validator.validate(payload)
