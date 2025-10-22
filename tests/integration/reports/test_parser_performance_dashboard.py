"""Integration tests for Parser Performance Dashboard report.

Tests verify the current f-string SQL implementation behavior as a baseline
before refactoring to Query Builder. These tests should pass with current code
and continue passing after refactoring.

Test Coverage:
- Date filter combinations (from_date, to_date, defaults)
- Telegram user ID filtering
- Model name filtering
- 90-day limit enforcement
- Cache behavior
- Error handling
- Success rate calculations
- Average metrics (confidence, response time, cost)
- Column structure and data types
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_frappe_for_parser_dashboard():
    """Mock frappe module for Parser Performance Dashboard tests with Query Builder support."""
    import types

    frappe_mock = MagicMock()

    # Mock common frappe methods
    frappe_mock._ = lambda x: x
    frappe_mock.throw = MagicMock(side_effect=Exception)
    frappe_mock.log_error = MagicMock()

    # Mock utils
    frappe_mock.utils = MagicMock()
    frappe_mock.utils.getdate = MagicMock(return_value=date(2025, 1, 31))

    # Mock add_days() function
    def mock_add_days(base_date, days):
        if isinstance(base_date, str):
            base_date = date.fromisoformat(base_date)
        return base_date + timedelta(days=days)

    frappe_mock.utils.add_days.side_effect = mock_add_days

    # Mock cache
    cache_mock = MagicMock()
    cache_mock.get = MagicMock(return_value=None)
    cache_mock.get_value = MagicMock(return_value=None)
    cache_mock.set = MagicMock()
    cache_mock.set_value = MagicMock()
    frappe_mock.cache = MagicMock(return_value=cache_mock)

    # Mock database
    frappe_mock.db = MagicMock()
    frappe_mock.db.sql = MagicMock(return_value=[])

    # Preserve any pre-existing modules
    prev = {
        m: sys.modules[m]
        for m in (
            "frappe",
            "frappe.utils",
            "frappe.query_builder",
            "frappe.query_builder.functions",
            "pypika",
            "pypika.terms",
        )
        if m in sys.modules
    }

    # Ensure the report module is freshly imported
    for m in list(sys.modules):
        if m.startswith("flrts_extensions.flrts.report.parser_performance_dashboard"):
            del sys.modules[m]

    # Register frappe + utils
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils

    # Stub minimal Query Builder
    query = MagicMock()
    query.select.return_value = query
    query.where.return_value = query
    query.groupby.return_value = query
    query.orderby.return_value = query
    # Make qb.run() return whatever db.sql would have returned
    query.run.side_effect = lambda as_dict=True: frappe_mock.db.sql.return_value

    qb = MagicMock()
    qb.from_.return_value = query
    qb.desc = "DESC"
    frappe_mock.qb = qb

    sys.modules["frappe.query_builder"] = types.SimpleNamespace(DocType=MagicMock())
    sys.modules["frappe.query_builder.functions"] = types.SimpleNamespace(
        Count=MagicMock(), Sum=MagicMock(), Avg=MagicMock(), Min=MagicMock()
    )
    sys.modules["pypika"] = types.SimpleNamespace(
        CustomFunction=lambda *_args, **_kwargs: MagicMock()
    )
    sys.modules["pypika.terms"] = types.SimpleNamespace(Case=MagicMock, Distinct=MagicMock())

    yield frappe_mock

    # Restore/cleanup modules
    for m in (
        "frappe",
        "frappe.utils",
        "frappe.query_builder",
        "frappe.query_builder.functions",
        "pypika",
        "pypika.terms",
    ):
        if m in prev:
            sys.modules[m] = prev[m]
        elif m in sys.modules:
            del sys.modules[m]

    # Drop report modules to avoid leaking state
    for m in list(sys.modules):
        if m.startswith("flrts_extensions.flrts.report.parser_performance_dashboard"):
            del sys.modules[m]


@pytest.mark.integration
def test_parser_dashboard_with_date_filters(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with explicit date filters."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    # Mock SQL response
    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 150,
            "accepted": 120,
            "rejected": 20,
            "pending": 10,
            "success_rate": Decimal("85.71"),
            "avg_confidence": Decimal("0.89"),
            "avg_response_ms": 1250,
            "avg_erpnext_response_ms": 450,
            "total_cost": Decimal("0.1250"),
            "avg_cost_per_parse": Decimal("0.0008"),
        },
        {
            "date": date(2025, 1, 30),
            "total_parses": 100,
            "accepted": 85,
            "rejected": 10,
            "pending": 5,
            "success_rate": Decimal("89.47"),
            "avg_confidence": Decimal("0.92"),
            "avg_response_ms": 1150,
            "avg_erpnext_response_ms": 400,
            "total_cost": Decimal("0.0850"),
            "avg_cost_per_parse": Decimal("0.0009"),
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL was called with correct parameters
    mock_frappe_for_parser_dashboard.db.sql.assert_called_once()
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args

    # Verify query structure
    query = call_args[0][0]
    assert "WHERE creation >= %(from_date)s AND creation <= %(to_date)s" in query
    assert "GROUP BY DATE(creation)" in query
    assert "ORDER BY date DESC" in query

    # Verify parameters
    params = call_args[0][1]
    assert params["from_date"] == "2025-01-01"
    assert params["to_date"] == "2025-01-31"

    # Verify column structure (11 columns)
    assert len(columns) == 11
    column_names = [col["fieldname"] for col in columns]
    assert "date" in column_names
    assert "total_parses" in column_names
    assert "accepted" in column_names
    assert "rejected" in column_names
    assert "pending" in column_names
    assert "success_rate" in column_names
    assert "avg_confidence" in column_names
    assert "avg_response_ms" in column_names
    assert "avg_erpnext_response_ms" in column_names
    assert "total_cost" in column_names
    assert "avg_cost_per_parse" in column_names

    # Verify data structure
    assert len(data) == 2
    assert data[0]["date"] == date(2025, 1, 31)
    assert data[0]["total_parses"] == 150
    assert data[0]["accepted"] == 120
    assert data[0]["rejected"] == 20
    assert data[0]["pending"] == 10
    assert data[0]["success_rate"] == Decimal("85.71")

    # Verify chart data
    assert chart is not None
    assert "data" in chart
    assert "type" in chart
    assert chart["type"] == "line"


@pytest.mark.integration
def test_parser_dashboard_with_user_filter(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with telegram_user_id filter."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-31",
        "telegram_user_id": "12345",
    }

    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 50,
            "accepted": 40,
            "rejected": 5,
            "pending": 5,
            "success_rate": Decimal("88.89"),
            "avg_confidence": Decimal("0.90"),
            "avg_response_ms": 1200,
            "avg_erpnext_response_ms": 420,
            "total_cost": Decimal("0.0500"),
            "avg_cost_per_parse": Decimal("0.0010"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes user filter
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "AND telegram_user_id = %(telegram_user_id)s" in query
    assert params["telegram_user_id"] == "12345"

    assert len(data) == 1
    assert data[0]["total_parses"] == 50


@pytest.mark.integration
def test_parser_dashboard_with_model_filter(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with model_name filter."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-31",
        "model_name": "gpt-4-turbo-preview",
    }

    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 75,
            "accepted": 65,
            "rejected": 8,
            "pending": 2,
            "success_rate": Decimal("89.04"),
            "avg_confidence": Decimal("0.93"),
            "avg_response_ms": 1400,
            "avg_erpnext_response_ms": 500,
            "total_cost": Decimal("0.0950"),
            "avg_cost_per_parse": Decimal("0.0013"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes model filter
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "AND model_name = %(model_name)s" in query
    assert params["model_name"] == "gpt-4-turbo-preview"

    assert len(data) == 1
    assert data[0]["total_parses"] == 75


@pytest.mark.integration
def test_parser_dashboard_default_filters(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with no filters (uses defaults)."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    mock_frappe_for_parser_dashboard.db.sql.return_value = []

    columns, data, message, chart = execute(None)

    # Verify default date range (last 30 days)
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    params = call_args[0][1]

    # from_date should be 30 days ago
    expected_from = date(2025, 1, 31) - timedelta(days=30)
    assert params["from_date"] == expected_from

    # to_date should be today
    assert params["to_date"] == date(2025, 1, 31)


@pytest.mark.integration
def test_parser_dashboard_90_day_limit(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard enforces 90-day limit."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    # Request 120-day range (should be capped to 90 days)
    filters = {"from_date": "2024-11-01", "to_date": "2025-01-31"}

    mock_frappe_for_parser_dashboard.db.sql.return_value = []

    columns, data, message, chart = execute(filters)

    # Verify from_date was adjusted to 90 days before to_date
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    params = call_args[0][1]

    # from_date should be adjusted to 90 days before to_date
    expected_from = date(2025, 1, 31) - timedelta(days=90)
    assert params["from_date"] == expected_from
    assert params["to_date"] == "2025-01-31"


@pytest.mark.integration
def test_parser_dashboard_cache_behavior(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard uses caching."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    # First call - no cache
    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 100,
            "accepted": 80,
            "rejected": 15,
            "pending": 5,
            "success_rate": Decimal("84.21"),
            "avg_confidence": Decimal("0.88"),
            "avg_response_ms": 1300,
            "avg_erpnext_response_ms": 480,
            "total_cost": Decimal("0.1000"),
            "avg_cost_per_parse": Decimal("0.0010"),
        }
    ]

    cache_mock = mock_frappe_for_parser_dashboard.cache.return_value

    columns, data, message, chart = execute(filters)

    # Verify cache was checked
    cache_mock.get_value.assert_called_once()
    cache_key = cache_mock.get_value.call_args[0][0]
    assert "parser_performance_dashboard" in cache_key
    assert "2025-01-01" in cache_key
    assert "2025-01-31" in cache_key

    # Verify cache was set
    cache_mock.set_value.assert_called_once()
    assert cache_mock.set_value.call_args[1]["expires_in_sec"] == 300  # 5 minutes


@pytest.mark.integration
def test_parser_dashboard_cache_hit(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard returns cached data when available."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    # Mock cache hit
    cached_data = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 100,
            "accepted": 80,
            "rejected": 15,
            "pending": 5,
            "success_rate": Decimal("84.21"),
            "avg_confidence": Decimal("0.88"),
            "avg_response_ms": 1300,
            "avg_erpnext_response_ms": 480,
            "total_cost": Decimal("0.1000"),
            "avg_cost_per_parse": Decimal("0.0010"),
        }
    ]

    cache_mock = mock_frappe_for_parser_dashboard.cache.return_value
    cache_mock.get_value.return_value = cached_data

    columns, data, message, chart = execute(filters)

    # Verify SQL was NOT called (cache hit)
    mock_frappe_for_parser_dashboard.db.sql.assert_not_called()

    # Verify cached data was returned
    assert len(data) == 1
    assert data[0]["total_parses"] == 100


@pytest.mark.integration
def test_parser_dashboard_error_handling(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard handles SQL errors gracefully."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    # Mock SQL error
    mock_frappe_for_parser_dashboard.db.sql.side_effect = Exception("Database connection error")

    columns, data, message, chart = execute(filters)

    # Verify error was logged
    mock_frappe_for_parser_dashboard.log_error.assert_called_once()
    error_message = mock_frappe_for_parser_dashboard.log_error.call_args[0][0]
    assert "Error in Parser Performance Dashboard" in error_message

    # Verify empty data returned (graceful degradation)
    assert data == []

    # Verify columns still returned
    assert len(columns) == 11


@pytest.mark.integration
def test_parser_dashboard_success_rate_calculation(mock_frappe_for_parser_dashboard):
    """Test success rate calculation formula in SQL."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    # Mock data with specific accepted/rejected counts
    # Success rate = (accepted / (accepted + rejected)) * 100
    # = (85 / (85 + 15)) * 100 = 85.00%
    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 110,
            "accepted": 85,
            "rejected": 15,
            "pending": 10,
            "success_rate": Decimal("85.00"),
            "avg_confidence": Decimal("0.88"),
            "avg_response_ms": 1300,
            "avg_erpnext_response_ms": 480,
            "total_cost": Decimal("0.1100"),
            "avg_cost_per_parse": Decimal("0.0010"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify success_rate calculation
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    query = call_args[0][0]

    # Verify SQL includes success rate CASE statement
    assert "CASE" in query
    assert "user_accepted = 'Accepted'" in query
    assert "user_accepted = 'Rejected'" in query
    assert "success_rate" in query

    # Verify returned success rate
    assert data[0]["success_rate"] == Decimal("85.00")


@pytest.mark.integration
def test_parser_dashboard_empty_result(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with no data."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    mock_frappe_for_parser_dashboard.db.sql.return_value = []

    columns, data, message, chart = execute(filters)

    # Verify columns returned
    assert len(columns) == 11

    # Verify empty data
    assert len(data) == 0

    # Verify chart handles empty data
    assert chart is None


@pytest.mark.integration
def test_parser_dashboard_avg_metrics(mock_frappe_for_parser_dashboard):
    """Test average metric calculations (confidence, response time, cost)."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 50,
            "accepted": 40,
            "rejected": 8,
            "pending": 2,
            "success_rate": Decimal("83.33"),
            "avg_confidence": Decimal("0.87"),
            "avg_response_ms": 1250,
            "avg_erpnext_response_ms": 450,
            "total_cost": Decimal("0.0500"),
            "avg_cost_per_parse": Decimal("0.0010"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes AVG functions
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    query = call_args[0][0]

    assert "AVG(confidence_score)" in query
    assert "AVG(response_duration_ms)" in query
    assert "AVG(erpnext_response_ms)" in query
    assert (
        "AVG(estimated_cost_usd)" in query
        or "SUM(estimated_cost_usd) / NULLIF(COUNT(*), 0)" in query
    )

    # Verify average metrics in data
    assert data[0]["avg_confidence"] == Decimal("0.87")
    assert data[0]["avg_response_ms"] == 1250
    assert data[0]["avg_erpnext_response_ms"] == 450
    assert data[0]["avg_cost_per_parse"] == Decimal("0.0010")


@pytest.mark.integration
def test_parser_dashboard_chart_structure(mock_frappe_for_parser_dashboard):
    """Test chart data structure for line chart."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {"from_date": "2025-01-01", "to_date": "2025-01-31"}

    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 100,
            "accepted": 85,
            "rejected": 10,
            "pending": 5,
            "success_rate": Decimal("89.47"),
            "avg_confidence": Decimal("0.90"),
            "avg_response_ms": 1200,
            "avg_erpnext_response_ms": 420,
            "total_cost": Decimal("0.1000"),
            "avg_cost_per_parse": Decimal("0.0010"),
        },
        {
            "date": date(2025, 1, 30),
            "total_parses": 80,
            "accepted": 70,
            "rejected": 8,
            "pending": 2,
            "success_rate": Decimal("89.74"),
            "avg_confidence": Decimal("0.91"),
            "avg_response_ms": 1150,
            "avg_erpnext_response_ms": 410,
            "total_cost": Decimal("0.0800"),
            "avg_cost_per_parse": Decimal("0.0010"),
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify chart structure
    assert chart is not None
    assert chart["type"] == "line"
    assert "data" in chart
    assert "labels" in chart["data"]
    assert "datasets" in chart["data"]

    # Verify chart shows success rate
    assert len(chart["data"]["datasets"]) == 1
    assert chart["data"]["datasets"][0]["name"] == "Success Rate (%)"

    # Verify labels match dates
    assert len(chart["data"]["labels"]) == 2
    assert chart["data"]["labels"][0] == "2025-01-31"
    assert chart["data"]["labels"][1] == "2025-01-30"

    # Verify values match success rates
    assert chart["data"]["datasets"][0]["values"][0] == Decimal("89.47")
    assert chart["data"]["datasets"][0]["values"][1] == Decimal("89.74")


@pytest.mark.integration
def test_parser_dashboard_multiple_filters(mock_frappe_for_parser_dashboard):
    """Test Parser Performance Dashboard with multiple filters combined."""
    from flrts_extensions.flrts.report.parser_performance_dashboard.parser_performance_dashboard import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-31",
        "telegram_user_id": "12345",
        "model_name": "gpt-4-turbo-preview",
    }

    mock_frappe_for_parser_dashboard.db.sql.return_value = [
        {
            "date": date(2025, 1, 31),
            "total_parses": 25,
            "accepted": 22,
            "rejected": 2,
            "pending": 1,
            "success_rate": Decimal("91.67"),
            "avg_confidence": Decimal("0.94"),
            "avg_response_ms": 1350,
            "avg_erpnext_response_ms": 470,
            "total_cost": Decimal("0.0325"),
            "avg_cost_per_parse": Decimal("0.0013"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes all filters
    call_args = mock_frappe_for_parser_dashboard.db.sql.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "creation >= %(from_date)s AND creation <= %(to_date)s" in query
    assert "AND telegram_user_id = %(telegram_user_id)s" in query
    assert "AND model_name = %(model_name)s" in query

    assert params["from_date"] == "2025-01-01"
    assert params["to_date"] == "2025-01-31"
    assert params["telegram_user_id"] == "12345"
    assert params["model_name"] == "gpt-4-turbo-preview"
