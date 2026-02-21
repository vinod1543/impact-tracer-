"""API module for demo payments service."""

from demo.payments_service.validator import BasePaymentValidator


def process_payment(payload: dict) -> bool:
    """Process payment payload via validator.

    Args:
        payload: Payment payload.

    Returns:
        bool: Validation status.
    """
    validator = BasePaymentValidator()
    return validator.validate(payload)
