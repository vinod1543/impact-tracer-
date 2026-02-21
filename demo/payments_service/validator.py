"""Validator module for demo payment service.

Contains validation logic used by both API and worker layers.
Changes here impact every code path that processes payments.
"""

from demo.payments_service.config import PaymentConfig, load_config
from demo.payments_service.models import PaymentRequest, RefundRequest


class BasePaymentValidator:
    """Validates payment payloads against business rules."""

    def __init__(self, config: PaymentConfig | None = None) -> None:
        """Initialize validator with configuration.

        Args:
            config: Payment configuration. Defaults to global config.
        """
        self.config = config or load_config()

    def validate(self, payment_data: dict) -> bool:
        """Validate a payment payload.

        Args:
            payment_data: Raw payment payload.

        Returns:
            bool: True when required fields are present.
        """
        return "amount" in payment_data and "currency" in payment_data

    def validate_amount(self, amount: float) -> bool:
        """Validate payment amount is within allowed range.

        Args:
            amount: Payment amount.

        Returns:
            bool: True if amount is within config limits.
        """
        return self.config.min_payment_amount <= amount <= self.config.max_payment_amount

    def validate_currency(self, currency: str) -> bool:
        """Validate currency is supported.

        Args:
            currency: Currency code.

        Returns:
            bool: True if currency is in supported list.
        """
        return currency in self.config.supported_currencies


class PaymentRequestValidator(BasePaymentValidator):
    """Full validation for structured PaymentRequest objects."""

    def validate_request(self, request: PaymentRequest) -> list[str]:
        """Validate a PaymentRequest and return list of errors.

        Args:
            request: Structured payment request.

        Returns:
            list[str]: List of validation error messages. Empty if valid.
        """
        errors = []
        if not self.validate_amount(request.amount):
            errors.append(
                f"Amount {request.amount} outside range "
                f"[{self.config.min_payment_amount}, {self.config.max_payment_amount}]"
            )
        if not self.validate_currency(request.currency):
            errors.append(f"Unsupported currency: {request.currency}")
        if not request.merchant_id:
            errors.append("Missing merchant_id")
        if not request.customer_email or "@" not in request.customer_email:
            errors.append("Invalid customer_email")
        return errors


class RefundValidator(BasePaymentValidator):
    """Validates refund requests."""

    def validate_refund(self, refund: RefundRequest, original_amount: float) -> list[str]:
        """Validate a refund request against the original payment.

        Args:
            refund: Refund request payload.
            original_amount: Original payment amount.

        Returns:
            list[str]: List of validation errors.
        """
        errors = []
        if not refund.payment_id:
            errors.append("Missing payment_id for refund")
        if not refund.reason:
            errors.append("Refund reason is required")
        if refund.partial_amount is not None:
            if refund.partial_amount <= 0:
                errors.append("Partial refund amount must be positive")
            if refund.partial_amount > original_amount:
                errors.append("Partial refund exceeds original amount")
        return errors
