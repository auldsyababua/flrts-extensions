"""
Logging utilities with NODE_ENV guards for production safety.

Implements environment-aware logging to prevent verbose logs in test/production.
"""
import os


def log_debug(message: str, logger_name: str = "flrts_extensions"):
    """
    Log debug message only in development environment.

    Suppressed when NODE_ENV is 'test' or 'production' to avoid log pollution.

    Args:
        message: Debug message to log
        logger_name: Logger namespace (default: "flrts_extensions")

    Example:
        >>> log_debug("Processing chat_id: 123456")  # Only logs if NODE_ENV != test|production
    """
    try:
        import frappe
    except ImportError:
        # Running outside Frappe context (e.g., unit tests)
        return

    env = os.getenv("NODE_ENV", "development")

    # Suppress debug logs in test and production
    if env not in ["test", "production"]:
        frappe.logger(logger_name).debug(message)


def log_info(message: str, logger_name: str = "flrts_extensions"):
    """
    Log info message (allowed in all environments).

    Info-level logs are useful for operational tracking and not suppressed.

    Args:
        message: Info message to log
        logger_name: Logger namespace (default: "flrts_extensions")

    Example:
        >>> log_info("Task ABC-123 updated to status: Completed")
    """
    try:
        import frappe
    except ImportError:
        return

    frappe.logger(logger_name).info(message)


def log_error(message: str, title: str = "Automation Error"):
    """
    Log error via Frappe Error Log (always logged, never suppressed).

    Errors are critical and must be tracked in all environments for debugging.

    Args:
        message: Error message/traceback
        title: Error title for grouping in Error Log

    Example:
        >>> log_error("Failed to send Telegram message: Connection refused", title="Telegram Send Failed")
    """
    try:
        import frappe
    except ImportError:
        return

    frappe.log_error(message=message, title=title)
