"""Utility module for demo payments service."""


def format_amount(amount: float) -> str:
    """Format numeric amount for display.

    Args:
        amount: Monetary amount.

    Returns:
        str: Formatted amount string.
    """
    return f"${amount:.2f}"
