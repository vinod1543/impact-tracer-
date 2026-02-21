"""Demo payments service package.

A realistic multi-module payment processing service used to demonstrate
Impact Tracer's static analysis, dependency graphing, and risk scoring.

Modules:
    models      - Data models (PaymentRequest, PaymentResponse, etc.)
    config      - Service configuration and feature flags
    validator   - Payment validation logic
    utils       - Shared utilities (formatting, hashing, retry)
    repository  - Database/persistence layer
    api         - HTTP API handlers
    worker      - Background job processing
    middleware  - Request middleware (auth, rate limiting, logging)
    notification- Downstream notification service
"""
