"""Data models for the payments service.

Contains Pydantic-like data classes representing the payment domain.
These models flow through every layer: API → validation → business logic → persistence.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class PaymentStatus(str, Enum):
    """Lifecycle status of a payment."""

    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


@dataclass
class PaymentRequest:
    """Incoming payment request from the API layer.

    Attributes:
        amount: Payment amount in smallest currency unit.
        currency: ISO currency code.
        merchant_id: Merchant identifier.
        customer_email: Customer email for receipts.
        metadata: Optional key-value metadata.
        idempotency_key: Client-provided dedup key.
    """

    amount: float
    currency: str
    merchant_id: str
    customer_email: str
    metadata: dict = field(default_factory=dict)
    idempotency_key: Optional[str] = None


@dataclass
class PaymentResponse:
    """API response returned after payment processing.

    Attributes:
        payment_id: System-generated payment identifier.
        status: Current payment status.
        amount_formatted: Human-readable amount string.
        risk_flag: Whether the payment was flagged for risk.
        message: Human-readable status message.
    """

    payment_id: str
    status: PaymentStatus
    amount_formatted: str
    risk_flag: bool = False
    message: str = ""


@dataclass
class TransactionRecord:
    """Persistence model for a completed transaction.

    Attributes:
        transaction_id: Unique transaction identifier.
        payment_id: Associated payment identifier.
        amount: Transaction amount.
        currency: Transaction currency.
        merchant_id: Merchant identifier.
        status: Transaction status.
        audit_hash: Integrity hash for audit trail.
    """

    transaction_id: str
    payment_id: str
    amount: float
    currency: str
    merchant_id: str
    status: PaymentStatus
    audit_hash: str = ""


@dataclass
class RefundRequest:
    """Request to refund a completed payment.

    Attributes:
        payment_id: Original payment to refund.
        reason: Refund reason.
        partial_amount: Optional partial refund amount.
    """

    payment_id: str
    reason: str
    partial_amount: Optional[float] = None


@dataclass
class NotificationPayload:
    """Payload sent to the notification service.

    Attributes:
        recipient_email: Notification recipient.
        subject: Notification subject.
        body: Notification body.
        payment_id: Associated payment.
        event_type: Type of event triggering notification.
    """

    recipient_email: str
    subject: str
    body: str
    payment_id: str
    event_type: str = "payment_completed"
