"""Repository layer for payment persistence.

Handles storage and retrieval of payment and transaction records.
Used by both the API layer (synchronous) and worker layer (async jobs).
"""

from __future__ import annotations

from demo.payments_service.models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    TransactionRecord,
)
from demo.payments_service.utils import (
    compute_audit_hash,
    generate_payment_id,
    generate_transaction_id,
    format_amount,
)


class PaymentRepository:
    """In-memory payment persistence store.

    In production this would be backed by a database.
    """

    def __init__(self) -> None:
        """Initialize empty stores."""
        self._payments: dict[str, PaymentResponse] = {}
        self._transactions: dict[str, TransactionRecord] = {}
        self._idempotency_cache: dict[str, str] = {}

    def check_idempotency(self, key: str) -> PaymentResponse | None:
        """Check if an idempotency key was already processed.

        Args:
            key: Client-provided idempotency key.

        Returns:
            PaymentResponse | None: Existing response if found.
        """
        payment_id = self._idempotency_cache.get(key)
        if payment_id:
            return self._payments.get(payment_id)
        return None

    def save_payment(self, request: PaymentRequest, status: PaymentStatus, risk_flag: bool = False) -> PaymentResponse:
        """Persist a payment and return response.

        Args:
            request: Original payment request.
            status: Resulting payment status.
            risk_flag: Whether payment was flagged.

        Returns:
            PaymentResponse: Stored payment response.
        """
        payment_id = generate_payment_id()
        response = PaymentResponse(
            payment_id=payment_id,
            status=status,
            amount_formatted=format_amount(request.amount),
            risk_flag=risk_flag,
            message=f"Payment {status.value}",
        )
        self._payments[payment_id] = response

        if request.idempotency_key:
            self._idempotency_cache[request.idempotency_key] = payment_id

        return response

    def save_transaction(self, payment_id: str, request: PaymentRequest) -> TransactionRecord:
        """Create and persist a transaction record.

        Args:
            payment_id: Associated payment identifier.
            request: Original payment request.

        Returns:
            TransactionRecord: Persisted transaction record.
        """
        txn_id = generate_transaction_id()
        audit_hash = compute_audit_hash(payment_id, request.amount, request.currency)
        record = TransactionRecord(
            transaction_id=txn_id,
            payment_id=payment_id,
            amount=request.amount,
            currency=request.currency,
            merchant_id=request.merchant_id,
            status=PaymentStatus.COMPLETED,
            audit_hash=audit_hash,
        )
        self._transactions[txn_id] = record
        return record

    def get_payment(self, payment_id: str) -> PaymentResponse | None:
        """Retrieve a payment by ID.

        Args:
            payment_id: Payment identifier.

        Returns:
            PaymentResponse | None: Payment if found.
        """
        return self._payments.get(payment_id)

    def update_payment_status(self, payment_id: str, status: PaymentStatus) -> bool:
        """Update the status of an existing payment.

        Args:
            payment_id: Payment identifier.
            status: New status.

        Returns:
            bool: True if payment was found and updated.
        """
        payment = self._payments.get(payment_id)
        if payment is None:
            return False
        payment.status = status
        payment.message = f"Payment {status.value}"
        return True

    def list_transactions_for_payment(self, payment_id: str) -> list[TransactionRecord]:
        """List all transactions for a given payment.

        Args:
            payment_id: Payment identifier.

        Returns:
            list[TransactionRecord]: Matching transactions.
        """
        return [txn for txn in self._transactions.values() if txn.payment_id == payment_id]
