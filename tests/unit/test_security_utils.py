"""Unit tests for security utilities."""

from flrts_extensions.utils.security import mask_secret


def test_mask_secret_basic():
    """Test basic secret masking functionality."""
    secret = "my_secret_key_12345"
    masked = mask_secret(secret)

    # Actual implementation shows all middle chars as asterisks
    assert masked.startswith("my")
    assert masked.endswith("45")
    assert "secret_key" not in masked


def test_mask_secret_short():
    """Test masking of short secrets (< 6 chars)."""
    secret = "abc"
    masked = mask_secret(secret)

    assert masked == "***"


def test_mask_secret_empty():
    """Test masking of empty string."""
    secret = ""
    masked = mask_secret(secret)

    assert masked == "***"


def test_mask_secret_none():
    """Test masking of None value."""
    masked = mask_secret(None)

    assert masked == "***"


def test_mask_secret_exact_six_chars():
    """Test masking of exactly 6 character secret."""
    secret = "123456"
    masked = mask_secret(secret)

    # Minimum 6 chars shows first 2, last 2, with asterisks in between
    assert masked.startswith("12")
    assert masked.endswith("56")
    assert len(masked) >= 6
