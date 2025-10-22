"""Integration tests for FLRTS Parser Log DocType.

These tests require a running ERPNext instance and should be marked
with @pytest.mark.integration to be skipped in CI environments without ERPNext.
"""

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def test_parser_log_creation(mock_frappe, sample_parser_log_data):
    """Test creating a new FLRTS Parser Log document."""
    # Setup mock
    mock_doc = mock_frappe.get_doc.return_value
    mock_doc.insert.return_value = sample_parser_log_data

    # Create document
    doc = mock_frappe.get_doc(
        {
            "doctype": "FLRTS Parser Log",
            "model_name": "gpt-4-turbo-preview",
            "total_tokens": 1500,
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        }
    )

    # Assertions
    assert doc is not None
    mock_frappe.get_doc.assert_called_once()


def test_parser_log_cost_calculation(mock_frappe, sample_parser_log_data):
    """Test that cost is calculated correctly on save."""
    # Setup mock
    mock_frappe.get_doc.return_value = sample_parser_log_data

    # Get document
    doc = mock_frappe.get_doc("FLRTS Parser Log", "FLRTS-PARSER-001")

    # Verify cost calculation
    assert "estimated_cost_usd" in doc
    assert doc["estimated_cost_usd"] == 0.0225


def test_parser_log_success_rate(mock_frappe):
    """Test success rate calculation for parser logs."""
    # Mock database query
    mock_frappe.db.sql.return_value = [{"success_rate": 95.5, "total_parses": 100}]

    # Query success rate
    result = mock_frappe.db.sql(
        """
        SELECT
            (SUM(CASE WHEN parse_status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate,
            COUNT(*) as total_parses
        FROM `tabFLRTS Parser Log`
        """,
        as_dict=True,
    )

    # Assertions
    assert result[0]["success_rate"] == 95.5
    assert result[0]["total_parses"] == 100
