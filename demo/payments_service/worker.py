"""Background worker module for demo payments service."""

from demo.payments_service.api import process_payment


def run_worker_job(job_payload: dict) -> bool:
    """Run a payment worker job.

    Args:
        job_payload: Worker input payload.

    Returns:
        bool: Processing result.
    """
    return process_payment(job_payload)
