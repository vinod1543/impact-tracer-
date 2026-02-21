"""Notification service for payment events.

Sends email/webhook notifications after payment lifecycle events.
Downstream consumer of the API and worker layers.
"""

from __future__ import annotations

from demo.payments_service.config import PaymentConfig, load_config
from demo.payments_service.models import (
    NotificationPayload,
    PaymentResponse,
    PaymentStatus,
)
from demo.payments_service.utils import format_amount, mask_email


class NotificationService:
    """Handles sending notifications for payment events.

    Called by API layer after payment completion and by worker for async notifications.
    """

    def __init__(self, config: PaymentConfig | None = None) -> None:
        self.config = config or load_config()
        self._sent: list[NotificationPayload] = []

    def send_payment_confirmation(self, payment: PaymentResponse, customer_email: str) -> bool:
        """Send payment confirmation notification.

        Args:
            payment: Payment response with status.
            customer_email: Recipient email.

        Returns:
            bool: True if notification was sent.
        """
        if not self.config.enable_notifications:
            return False

        payload = NotificationPayload(
            recipient_email=customer_email,
            subject=f"Payment {payment.status.value} - {payment.amount_formatted}",
            body=self._build_confirmation_body(payment),
            payment_id=payment.payment_id,
            event_type="payment_confirmation",
        )
        return self._dispatch(payload)

    def send_refund_notification(self, payment_id: str, amount: float, customer_email: str) -> bool:
        """Send refund notification.

        Args:
            payment_id: Refunded payment identifier.
            amount: Refund amount.
            customer_email: Recipient email.

        Returns:
            bool: True if notification was sent.
        """
        if not self.config.enable_notifications:
            return False

        payload = NotificationPayload(
            recipient_email=customer_email,
            subject=f"Refund Processed - {format_amount(amount)}",
            body=f"A refund of {format_amount(amount)} has been processed for payment {payment_id}.",
            payment_id=payment_id,
            event_type="refund_notification",
        )
        return self._dispatch(payload)

    def send_risk_alert(self, payment: PaymentResponse, merchant_id: str) -> bool:
        """Send risk alert to operations team.

        Args:
            payment: Flagged payment.
            merchant_id: Associated merchant.

        Returns:
            bool: True if alert was sent.
        """
        payload = NotificationPayload(
            recipient_email="ops-alerts@payments.internal",
            subject=f"Risk Alert: Payment {payment.payment_id} flagged",
            body=f"Payment {payment.payment_id} ({payment.amount_formatted}) from merchant {merchant_id} was flagged for risk review.",
            payment_id=payment.payment_id,
            event_type="risk_alert",
        )
        return self._dispatch(payload)

    def _build_confirmation_body(self, payment: PaymentResponse) -> str:
        """Build confirmation email body.

        Args:
            payment: Payment response.

        Returns:
            str: Email body text.
        """
        return (
            f"Your payment {payment.payment_id} of {payment.amount_formatted} "
            f"has been {payment.status.value.lower()}."
        )

    def _dispatch(self, payload: NotificationPayload) -> bool:
        """Dispatch notification payload (stub).

        Args:
            payload: Notification to send.

        Returns:
            bool: True on success.
        """
        self._sent.append(payload)
        return True

    def get_sent_notifications(self) -> list[NotificationPayload]:
        """Return all sent notifications for debugging.

        Returns:
            list[NotificationPayload]: All dispatched notifications.
        """
        return list(self._sent)
