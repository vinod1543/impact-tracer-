"""Validator module for demo payment service."""


class BasePaymentValidator:
    """Validates payment payloads."""

    def validate(self, payment_data: dict) -> bool:
        """Validate a payment payload.

        Args:
            payment_data: Raw payment payload.

        Returns:
            bool: True when required fields are present.
        """
        return "amount" in payment_data and "currency" in payment_data
