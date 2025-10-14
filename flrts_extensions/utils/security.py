"""
Security utilities for secret masking and secure handling.

Implements two-character reveal policy for secrets in logs.
"""


def mask_secret(secret: str, reveal_chars: int = 2) -> str:
    """
    Mask secret with two-character reveal (first N + last N characters).

    Two-character reveal policy:
    - Secrets >= 6 chars: Show first 2 + last 2 (e.g., "ab******d2")
    - Secrets < 6 chars: Return "***" (insufficient length for safe reveal)
    - Empty/None: Return "***"

    Args:
        secret: The secret string to mask
        reveal_chars: Number of chars to reveal on each end (default: 2)

    Returns:
        Masked string following two-character policy

    Examples:
        >>> mask_secret("6234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw")
        '62**************aw'

        >>> mask_secret("short")
        '***'

        >>> mask_secret("")
        '***'

        >>> mask_secret(None)
        '***'
    """
    # Handle None, empty, or too-short secrets
    if not secret or len(secret) < 6:
        return "***"

    # Extract prefix and suffix
    prefix = secret[:reveal_chars]
    suffix = secret[-reveal_chars:]

    # Calculate mask length
    mask_len = len(secret) - (reveal_chars * 2)

    # Return masked string
    return f"{prefix}{'*' * mask_len}{suffix}"
