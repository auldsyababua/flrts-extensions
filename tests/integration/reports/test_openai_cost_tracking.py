"""Integration tests for OpenAI Cost Tracking report.

Tests verify the current f-string SQL implementation behavior as a baseline
before refactoring to Query Builder. These tests should pass with current code
and continue passing after refactoring.

Test Coverage:
- Date filter combinations (from_date, to_date, defaults)
- Model name filtering
- Group by Date vs Model Name
- Summary row calculations
- Projected monthly cost calculations
- Budget status indicators
- Column structure and data types
"""

import sys
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_frappe_for_cost_tracking():
    """Mock frappe module for OpenAI Cost Tracking tests.

    Provides proper mocking of frappe.db.sql, frappe.utils functions,
    and frappe translation (_).
    """
    frappe_mock = MagicMock()

    # Mock translation function
    frappe_mock._.side_effect = lambda x: x

    # Mock getdate() to return consistent date
    frappe_mock.utils.getdate.return_value = date(2025, 1, 15)

    # Mock get_last_day() to return last day of January
    frappe_mock.utils.get_last_day.return_value = date(2025, 1, 31)

    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils

    yield frappe_mock

    del sys.modules["frappe"]
    del sys.modules["frappe.utils"]


@pytest.mark.integration
def test_openai_cost_tracking_with_date_filters(mock_frappe_for_cost_tracking):
    """Test OpenAI Cost Tracking report with explicit date filters."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15", "group_by": "Date"}

    # Mock SQL response with sample data
    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 100,
            "total_tokens": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
            "total_cost": Decimal("0.0250"),
            "avg_cost_per_request": Decimal("0.000250"),
            "model_name": "gpt-4-turbo-preview",
        },
        {
            "date": date(2025, 1, 14),
            "total_requests": 50,
            "total_tokens": 2500,
            "prompt_tokens": 1500,
            "completion_tokens": 1000,
            "total_cost": Decimal("0.0125"),
            "avg_cost_per_request": Decimal("0.000250"),
            "model_name": "gpt-4-turbo-preview",
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL was called with correct parameters
    mock_frappe_for_cost_tracking.db.sql.assert_called_once()
    call_args = mock_frappe_for_cost_tracking.db.sql.call_args

    # Verify query contains expected conditions
    query = call_args[0][0]
    assert "WHERE creation >= %(from_date)s AND creation <= %(to_date)s" in query
    assert "GROUP BY DATE(creation)" in query or "GROUP BY date" in query.lower()
    assert "ORDER BY date DESC" in query

    # Verify parameters
    params = call_args[0][1]
    assert params["from_date"] == "2025-01-01"
    assert params["to_date"] == "2025-01-15"

    # Verify column structure (10 columns total)
    assert len(columns) == 10
    column_names = [col["fieldname"] for col in columns]
    assert "date" in column_names
    assert "total_requests" in column_names
    assert "total_tokens" in column_names
    assert "prompt_tokens" in column_names
    assert "completion_tokens" in column_names
    assert "total_cost" in column_names
    assert "avg_cost_per_request" in column_names
    assert "model_name" in column_names
    assert "projected_monthly_cost" in column_names
    assert "budget_status" in column_names

    # Verify data structure (2 data rows + 1 summary row)
    assert len(data) == 3

    # Verify first row data
    assert data[0]["date"] == date(2025, 1, 15)
    assert data[0]["total_requests"] == 100
    assert data[0]["total_tokens"] == 5000
    assert data[0]["total_cost"] == Decimal("0.0250")

    # Verify projected monthly cost calculation
    # (total_cost / current_day) * days_in_month
    # (0.025 / 15) * 31 = 0.0517 (rounded to 4 decimals)
    assert "projected_monthly_cost" in data[0]
    assert isinstance(data[0]["projected_monthly_cost"], (int, float, Decimal))

    # Verify budget status
    assert data[0]["budget_status"] in ["⚠️ Over Budget", "✅ Under Budget"]
    assert "indicator" in data[0]

    # Verify summary row (last row with date='Total')
    summary_row = data[-1]
    assert summary_row["date"] == "Total"
    assert summary_row["total_requests"] == 150  # 100 + 50
    assert summary_row["total_tokens"] == 7500  # 5000 + 2500
    assert summary_row["model_name"] == ""

    # Verify chart data
    assert chart is not None
    assert "data" in chart
    assert "labels" in chart["data"]
    assert "datasets" in chart["data"]


@pytest.mark.integration
def test_openai_cost_tracking_with_model_filter(mock_frappe_for_cost_tracking):
    """Test OpenAI Cost Tracking with model_name filter."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-15",
        "model_name": "gpt-4",
        "group_by": "Date",
    }

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 25,
            "total_tokens": 1250,
            "prompt_tokens": 750,
            "completion_tokens": 500,
            "total_cost": Decimal("0.0100"),
            "avg_cost_per_request": Decimal("0.000400"),
            "model_name": "gpt-4",
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL was called with model filter
    call_args = mock_frappe_for_cost_tracking.db.sql.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "AND model_name = %(model_name)s" in query
    assert params["model_name"] == "gpt-4"

    # Verify filtered data
    assert len(data) == 2  # 1 data row + 1 summary row
    assert data[0]["model_name"] == "gpt-4"


@pytest.mark.integration
def test_openai_cost_tracking_group_by_model(mock_frappe_for_cost_tracking):
    """Test OpenAI Cost Tracking grouped by Model Name."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-15",
        "group_by": "Model Name",
    }

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 100,
            "total_tokens": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
            "total_cost": Decimal("0.0500"),
            "avg_cost_per_request": Decimal("0.000500"),
            "model_name": "gpt-4-turbo-preview",
        },
        {
            "date": date(2025, 1, 15),
            "total_requests": 200,
            "total_tokens": 8000,
            "prompt_tokens": 5000,
            "completion_tokens": 3000,
            "total_cost": Decimal("0.0200"),
            "avg_cost_per_request": Decimal("0.000100"),
            "model_name": "gpt-3.5-turbo",
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL groups by model_name
    call_args = mock_frappe_for_cost_tracking.db.sql.call_args
    query = call_args[0][0]
    assert "GROUP BY model_name" in query

    # Verify data grouped by model
    assert len(data) == 3  # 2 model rows + 1 summary
    assert data[0]["model_name"] == "gpt-4-turbo-preview"
    assert data[1]["model_name"] == "gpt-3.5-turbo"
    assert data[2]["date"] == "Total"


@pytest.mark.integration
def test_openai_cost_tracking_default_filters(mock_frappe_for_cost_tracking):
    """Test OpenAI Cost Tracking with no filters (uses defaults)."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    mock_frappe_for_cost_tracking.db.sql.return_value = []

    columns, data, message, chart = execute(None)

    # Verify default date range is applied
    call_args = mock_frappe_for_cost_tracking.db.sql.call_args
    params = call_args[0][1]

    # Default from_date should be first day of current month
    assert params["from_date"] == date(2025, 1, 1)
    # Default to_date should be today
    assert params["to_date"] == date(2025, 1, 15)


@pytest.mark.integration
def test_openai_cost_tracking_budget_status_over(mock_frappe_for_cost_tracking):
    """Test budget status indicator when cost exceeds $10."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 1000,
            "total_tokens": 50000,
            "prompt_tokens": 30000,
            "completion_tokens": 20000,
            "total_cost": Decimal("12.5000"),
            "avg_cost_per_request": Decimal("0.012500"),
            "model_name": "gpt-4-turbo-preview",
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify over-budget status
    assert data[0]["budget_status"] == "⚠️ Over Budget"
    assert data[0]["indicator"] == "red"


@pytest.mark.integration
def test_openai_cost_tracking_budget_status_under(mock_frappe_for_cost_tracking):
    """Test budget status indicator when cost is under $10."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 50,
            "total_tokens": 2500,
            "prompt_tokens": 1500,
            "completion_tokens": 1000,
            "total_cost": Decimal("5.0000"),
            "avg_cost_per_request": Decimal("0.100000"),
            "model_name": "gpt-4-turbo-preview",
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify under-budget status
    assert data[0]["budget_status"] == "✅ Under Budget"
    assert data[0]["indicator"] == "green"


@pytest.mark.integration
def test_openai_cost_tracking_empty_result(mock_frappe_for_cost_tracking):
    """Test OpenAI Cost Tracking with no data."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = []

    columns, data, message, chart = execute(filters)

    # Verify columns still returned
    assert len(columns) == 10

    # Verify empty data (no summary row for empty data)
    assert len(data) == 0

    # Verify chart handles empty data
    assert chart is None


@pytest.mark.integration
def test_openai_cost_tracking_summary_calculations(mock_frappe_for_cost_tracking):
    """Test summary row calculations are correct."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 100,
            "total_tokens": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
            "total_cost": Decimal("2.5000"),
            "avg_cost_per_request": Decimal("0.025000"),
            "model_name": "gpt-4",
        },
        {
            "date": date(2025, 1, 14),
            "total_requests": 50,
            "total_tokens": 2500,
            "prompt_tokens": 1500,
            "completion_tokens": 1000,
            "total_cost": Decimal("1.2500"),
            "avg_cost_per_request": Decimal("0.025000"),
            "model_name": "gpt-4",
        },
        {
            "date": date(2025, 1, 13),
            "total_requests": 25,
            "total_tokens": 1250,
            "prompt_tokens": 750,
            "completion_tokens": 500,
            "total_cost": Decimal("0.6250"),
            "avg_cost_per_request": Decimal("0.025000"),
            "model_name": "gpt-4",
        },
    ]

    columns, data, message, chart = execute(filters)

    # Get summary row (last row)
    summary = data[-1]

    # Verify summary calculations
    assert summary["date"] == "Total"
    assert summary["total_requests"] == 175  # 100 + 50 + 25
    assert summary["total_tokens"] == 8750  # 5000 + 2500 + 1250
    assert summary["prompt_tokens"] == 5250  # 3000 + 1500 + 750
    assert summary["completion_tokens"] == 3500  # 2000 + 1000 + 500
    assert summary["total_cost"] == 4.375  # 2.5 + 1.25 + 0.625 (rounded to 4 decimals)
    assert summary["avg_cost_per_request"] == round(
        4.375 / 175, 6
    )  # total_cost / total_requests
    assert summary["model_name"] == ""
    assert summary["budget_status"] == ""


@pytest.mark.integration
def test_openai_cost_tracking_projected_cost_calculation(mock_frappe_for_cost_tracking):
    """Test projected monthly cost calculation logic."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    # Current day is 15th, month has 31 days (mocked)
    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 100,
            "total_tokens": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
            "total_cost": Decimal("3.0000"),
            "avg_cost_per_request": Decimal("0.030000"),
            "model_name": "gpt-4",
        }
    ]

    columns, data, message, chart = execute(filters)

    # Projected cost = (3.0 / 15) * 31 = 6.2
    expected_projection = round((3.0 / 15) * 31, 4)

    assert data[0]["projected_monthly_cost"] == expected_projection


@pytest.mark.integration
def test_openai_cost_tracking_zero_cost_projection(mock_frappe_for_cost_tracking):
    """Test projected monthly cost when total_cost is zero or None."""
    from flrts_extensions.flrts.report.openai_cost_tracking.openai_cost_tracking import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-15"}

    mock_frappe_for_cost_tracking.db.sql.return_value = [
        {
            "date": date(2025, 1, 15),
            "total_requests": 100,
            "total_tokens": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
            "total_cost": None,  # No cost data
            "avg_cost_per_request": Decimal("0.000000"),
            "model_name": "gpt-4",
        }
    ]

    columns, data, message, chart = execute(filters)

    # Should handle None gracefully
    assert data[0]["projected_monthly_cost"] == 0
