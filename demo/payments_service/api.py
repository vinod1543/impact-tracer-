"""API module for demo payments service.

HTTP-facing API handlers for payment operations.
Orchestrates middleware, validation, persistence, and notifications.
"""

from demo.payments_service.config import PaymentConfig, load_config
from demo.payments_service.middleware import AuthMiddleware, RateLimiter, RequestLogger
from demo.payments_service.models import PaymentRequest, PaymentResponse, PaymentStatus, RefundRequest
from demo.payments_service.notification import NotificationService
from demo.payments_service.repository import PaymentRepository
from demo.payments_service.utils import format_amount
from demo.payments_service.validator import PaymentRequestValidator, RefundValidator


# Module-level singletons (simulating dependency injection)
_config = load_config()
_auth = AuthMiddleware()
_rate_limiter = RateLimiter()
_logger = RequestLogger()
_repo = PaymentRepository()
_validator = PaymentRequestValidator(config=_config)
_refund_validator = RefundValidator(config=_config)
_notifications = NotificationService(config=_config)


def process_payment(payload: dict) -> bool:
    """Process payment payload via validator (legacy simple API).

    Args:
        payload: Payment payload.

    Returns:
        bool: Validation status.
    """
    _ = format_amount(float(payload.get("amount", 0)))
    validator = PaymentRequestValidator()
    return validator.validate(payload)


def create_payment(request: PaymentRequest, api_key: str) -> PaymentResponse:
    """Full payment creation flow.

    Steps:
        1. Authenticate API key
        2. Rate limit check
        3. Log request
        4. Validate request
        5. Check idempotency
        6. Persist payment
        7. Send notifications

    Args:
        request: Structured payment request.
        api_key: Client API key.

    Returns:
        PaymentResponse: Payment result.

    Raises:
        PermissionError: If authentication fails.
        ValueError: If validation fails.
        RuntimeError: If rate limited.
    """
    # 1. Auth
    if not _auth.authenticate(api_key):
        raise PermissionError("Invalid API key")

    # 2. Rate limit
    merchant_id = _auth.extract_merchant_from_key(api_key)
    if not _rate_limiter.is_allowed(merchant_id):
        raise RuntimeError("Rate limit exceeded")

    # 3. Log
    _logger.log_request("/api/payments", merchant_id, request.customer_email)

    # 4. Validate
    errors = _validator.validate_request(request)
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    # 5. Idempotency
    if request.idempotency_key:
        existing = _repo.check_idempotency(request.idempotency_key)
        if existing:
            return existing

    # 6. Persist
    risk_flag = _assess_risk(request)
    status = PaymentStatus.COMPLETED if not risk_flag else PaymentStatus.PENDING
    response = _repo.save_payment(request, status, risk_flag)

    # 7. Notify
    if status == PaymentStatus.COMPLETED:
        _notifications.send_payment_confirmation(response, request.customer_email)
    if risk_flag:
        _notifications.send_risk_alert(response, request.merchant_id)

    return response


def get_payment(payment_id: str, api_key: str) -> PaymentResponse:
    """Retrieve payment by ID.

    Args:
        payment_id: Payment identifier.
        api_key: Client API key.

    Returns:
        PaymentResponse: Payment data.

    Raises:
        PermissionError: If auth fails.
        KeyError: If payment not found.
    """
    if not _auth.authenticate(api_key):
        raise PermissionError("Invalid API key")

    payment = _repo.get_payment(payment_id)
    if payment is None:
        raise KeyError(f"Payment not found: {payment_id}")
    return payment


def process_refund(refund: RefundRequest, api_key: str) -> PaymentResponse:
    """Process a refund request.

    Args:
        refund: Refund request.
        api_key: Client API key.

    Returns:
        PaymentResponse: Updated payment response.

    Raises:
        PermissionError: If auth fails.
        KeyError: If original payment not found.
        ValueError: If refund validation fails.
    """
    if not _auth.authenticate(api_key):
        raise PermissionError("Invalid API key")

    original = _repo.get_payment(refund.payment_id)
    if original is None:
        raise KeyError(f"Payment not found: {refund.payment_id}")

    original_amount = float(original.amount_formatted.replace("$", "").replace(",", ""))
    errors = _refund_validator.validate_refund(refund, original_amount)
    if errors:
        raise ValueError(f"Refund validation failed: {'; '.join(errors)}")

    _repo.update_payment_status(refund.payment_id, PaymentStatus.REFUNDED)

    refund_amount = refund.partial_amount or original_amount
    _notifications.send_refund_notification(refund.payment_id, refund_amount, "customer@example.com")

    return _repo.get_payment(refund.payment_id)


def _assess_risk(request: PaymentRequest) -> bool:
    """Simple risk assessment based on amount threshold.

    Args:
        request: Payment request.

    Returns:
        bool: True if payment is flagged as risky.
    """
    if not _config.enable_fraud_check:
        return False
    risk_score = request.amount / _config.max_payment_amount
    return risk_score > _config.risk_threshold
