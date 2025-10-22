"""Shared pytest fixtures for flrts-extensions tests.

This module provides common test fixtures including Frappe module mocking
for unit tests that don't require a full ERPNext instance.
"""

import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_frappe():
    """Mock frappe module for unit tests.

    This fixture creates a mock frappe module and injects it into sys.modules
    so that imports like 'import frappe' work in tests without requiring
    a full Frappe/ERPNext installation.

    Yields:
        MagicMock: Mock frappe module instance

    Example:
        def test_something(mock_frappe):
            mock_frappe.get_doc.return_value = {"name": "Test"}
            # Test code here
    """
    frappe_mock = MagicMock()
    sys.modules["frappe"] = frappe_mock
    yield frappe_mock
    del sys.modules["frappe"]


@pytest.fixture
def sample_parser_log_data():
    """Sample FLRTS Parser Log data for testing.

    Returns:
        dict: Sample parser log document data
    """
    return {
        "name": "FLRTS-PARSER-001",
        "creation": "2025-10-22 10:00:00",
        "model_name": "gpt-4-turbo-preview",
        "total_tokens": 1500,
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "estimated_cost_usd": 0.0225,
        "parse_status": "Success",
        "confidence_score": 0.95,
    }


@pytest.fixture
def sample_maintenance_visit_data():
    """Sample Maintenance Visit data for testing.

    Returns:
        dict: Sample maintenance visit document data
    """
    return {
        "name": "MV-001",
        "custom_assigned_to": "user@example.com",
        "custom_flrts_priority": "High",
        "custom_parse_confidence": 0.9,
        "custom_telegram_message_id": "12345",
        "custom_flrts_source": "telegram",
        "custom_flagged_for_review": 0,
    }
