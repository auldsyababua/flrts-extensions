"""
Unit tests for utility functions (security, logging).

Tests secret masking policy and logging guards.
"""
import pytest
from flrts_extensions.utils.security import mask_secret


class TestMaskSecret:
    """Test secret masking with two-character reveal policy."""

    def test_mask_long_secret(self):
        """Test masking for secrets >= 6 chars."""
        secret = "6234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
        result = mask_secret(secret)

        # Should reveal first 2 + last 2
        assert result.startswith("62")
        assert result.endswith("aw")
        assert "****" in result
        assert secret[2:-2] not in result  # Middle chars masked

    def test_mask_short_secret(self):
        """Test masking for secrets < 6 chars."""
        assert mask_secret("short") == "***"
        assert mask_secret("ab") == "***"
        assert mask_secret("12345") == "***"

    def test_mask_edge_cases(self):
        """Test edge cases: empty, None."""
        assert mask_secret("") == "***"
        assert mask_secret(None) == "***"

    def test_mask_exactly_six_chars(self):
        """Test masking for exactly 6-char secret."""
        secret = "abcdef"
        result = mask_secret(secret)

        # Should reveal first 2 + last 2
        assert result == "ab**ef"


# STUB: Add tests for logging guards when integrated with Frappe
# class TestLoggingGuards:
#     def test_debug_suppressed_in_test(self):
#         pass
#     def test_debug_allowed_in_dev(self):
#         pass
#     def test_error_always_logged(self):
#         pass
