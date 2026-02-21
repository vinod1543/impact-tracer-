"""Background worker module for demo payments service.

Handles async job processing: batch validation, retry, and notifications.
Depends on API, validator, repository, and notification layers.
"""

from demo.payments_service.api import process_payment, create_payment, _repo, _notifications
from demo.payments_service.config import load_config, PaymentConfig
from demo.payments_service.models import PaymentRequest, PaymentStatus
from demo.payments_service.notification import NotificationService
from demo.payments_service.repository import PaymentRepository
from demo.payments_service.utils import retry_with_backoff
from demo.payments_service.validator import BasePaymentValidator, PaymentRequestValidator


def run_worker_job(job_payload: dict) -> bool:
    """Run a payment worker job.

    Args:
        job_payload: Worker input payload.

    Returns:
        bool: Processing result.
    """
    return process_payment(job_payload)


def dry_run_validation(job_payload: dict) -> bool:
    """Run direct validation to simulate a second call path.

    Args:
        job_payload: Worker input payload.

    Returns:
        bool: Validation result.
    """
    validator = BasePaymentValidator()
    return validator.validate(job_payload)


def batch_validate_payments(payloads: list[dict]) -> dict:
    """Validate a batch of payment payloads.

    Args:
        payloads: List of payment payloads.

    Returns:
        dict: Results with counts of valid/invalid and per-payload errors.
    """
    validator = PaymentRequestValidator()
    results = {"valid": 0, "invalid": 0, "errors": []}
    for i, payload in enumerate(payloads):
        request = PaymentRequest(
            amount=payload.get("amount", 0),
            currency=payload.get("currency", ""),
            merchant_id=payload.get("merchant_id", ""),
            customer_email=payload.get("customer_email", ""),
        )
        errors = validator.validate_request(request)
        if errors:
            results["invalid"] += 1
            results["errors"].append({"index": i, "errors": errors})
        else:
            results["valid"] += 1
    return results


def process_payment_with_retry(request: PaymentRequest, api_key: str) -> dict:
    """Process a payment with automatic retry on failure.

    Args:
        request: Payment request.
        api_key: API key for authentication.

    Returns:
        dict: Result with payment_id and status.
    """
    def _attempt():
        return create_payment(request, api_key)

    try:
        response = retry_with_backoff(_attempt)
        return {"payment_id": response.payment_id, "status": response.status.value}
    except Exception as e:
        return {"payment_id": None, "status": "FAILED", "error": str(e)}


def process_pending_payments(repo: PaymentRepository | None = None) -> int:
    """Scan and process all pending payments.

    Args:
        repo: Payment repository (defaults to shared instance).

    Returns:
        int: Number of payments processed.
    """
    repository = repo or _repo
    processed = 0
    for payment_id, payment in list(repository._payments.items()):
        if payment.status == PaymentStatus.PENDING:
            repository.update_payment_status(payment_id, PaymentStatus.PROCESSING)
            # Simulate processing
            repository.update_payment_status(payment_id, PaymentStatus.COMPLETED)
            processed += 1
    return processed


def send_batch_notifications(repo: PaymentRepository | None = None, notifier: NotificationService | None = None) -> int:
    """Send notifications for all completed payments missing notifications.

    Args:
        repo: Payment repository.
        notifier: Notification service.

    Returns:
        int: Number of notifications sent.
    """
    repository = repo or _repo
    notification_service = notifier or _notifications
    sent = 0
    for payment_id, payment in repository._payments.items():
        if payment.status == PaymentStatus.COMPLETED:
            notification_service.send_payment_confirmation(payment, "batch@example.com")
            sent += 1
    return sent
