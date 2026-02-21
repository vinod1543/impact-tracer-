"""Background worker module for demo payments service."""

from demo.payments_service.api import process_payment
from demo.payments_service.validator import BasePaymentValidator


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
