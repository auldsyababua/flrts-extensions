"""Integration tests for Telegram Message Volume report.

Tests verify the current f-string SQL implementation behavior as a baseline
before refactoring to Query Builder. These tests should pass with current code
and continue passing after refactoring.

Test Coverage:
- Date filter combinations (from_date, to_date, defaults)
- Group by Date vs Hour
- Telegram user ID filtering
- 90-day limit enforcement
- Peak hour calculation
- Cache behavior
- Error handling
- Message metrics (total, unique users, tasks created, errors)
- Column structure and data types
"""

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_frappe_for_telegram_volume():
    """Mock frappe module for Telegram Message Volume tests.

    Provides proper mocking of frappe.db.sql, frappe.cache,
    frappe.throw, and error logging.
    """
    frappe_mock = MagicMock()

    # Mock translation function
    frappe_mock._.side_effect = lambda x: x

    # Mock frappe.throw for validation errors
    def mock_throw(message):
        raise Exception(message)

    frappe_mock.throw = mock_throw

    # Mock cache
    cache_mock = MagicMock()
    cache_mock.get.return_value = None  # No cache hit by default
    frappe_mock.cache.return_value = cache_mock

    # Mock log_error
    frappe_mock.log_error = MagicMock()

    sys.modules["frappe"] = frappe_mock

    yield frappe_mock

    del sys.modules["frappe"]


@pytest.mark.integration
def test_telegram_volume_group_by_date(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume grouped by Date."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    # Mock SQL response
    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 150,
            "unique_users": 12,
            "tasks_created": 45,
            "errors": 3,
            "avg_confidence": Decimal("0.89"),
        },
        {
            "date": date(2025, 1, 6),
            "total_messages": 120,
            "unique_users": 10,
            "tasks_created": 38,
            "errors": 2,
            "avg_confidence": Decimal("0.87"),
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL was called with correct parameters
    mock_frappe_for_telegram_volume.db.sql.assert_called_once()
    call_args = mock_frappe_for_telegram_volume.db.sql.call_args

    # Verify query structure for Date grouping
    query = call_args[0][0]
    assert "DATE(creation) as date" in query
    assert "GROUP BY DATE(creation)" in query
    assert "ORDER BY date DESC" in query
    assert "AVG(confidence_score)" in query  # Date grouping includes avg_confidence

    # Verify parameters
    params = call_args[0][1]
    assert params["from_date"] == "2025-01-01"
    assert params["to_date"] == "2025-01-07"

    # Verify column structure for Date grouping (6 columns)
    assert len(columns) == 6
    column_names = [col["fieldname"] for col in columns]
    assert "date" in column_names
    assert "total_messages" in column_names
    assert "unique_users" in column_names
    assert "tasks_created" in column_names
    assert "errors" in column_names
    assert "avg_confidence" in column_names

    # Verify data
    assert len(data) == 2
    assert data[0]["date"] == date(2025, 1, 7)
    assert data[0]["total_messages"] == 150
    assert data[0]["unique_users"] == 12
    assert data[0]["tasks_created"] == 45
    assert data[0]["errors"] == 3
    assert data[0]["avg_confidence"] == Decimal("0.89")

    # Verify chart
    assert chart is not None
    assert chart["type"] == "line"
    assert len(chart["data"]["labels"]) == 2


@pytest.mark.integration
def test_telegram_volume_group_by_hour(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume grouped by Hour."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-07",
        "to_date": "2025-01-07",
        "group_by": "Hour",
    }

    # Mock SQL response
    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "hour": 0,
            "total_messages": 5,
            "unique_users": 2,
            "tasks_created": 1,
            "errors": 0,
        },
        {
            "hour": 8,
            "total_messages": 45,
            "unique_users": 8,
            "tasks_created": 15,
            "errors": 1,
        },
        {
            "hour": 14,
            "total_messages": 60,
            "unique_users": 10,
            "tasks_created": 20,
            "errors": 2,
        },
        {
            "hour": 20,
            "total_messages": 40,
            "unique_users": 6,
            "tasks_created": 12,
            "errors": 0,
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL query for Hour grouping
    call_args = mock_frappe_for_telegram_volume.db.sql.call_args
    query = call_args[0][0]

    assert "HOUR(creation) as hour" in query
    assert "GROUP BY HOUR(creation)" in query
    assert "ORDER BY hour" in query
    assert "AVG(confidence_score)" not in query  # Hour grouping excludes avg_confidence

    # Verify column structure for Hour grouping (5 columns)
    assert len(columns) == 5
    column_names = [col["fieldname"] for col in columns]
    assert "hour" in column_names
    assert "total_messages" in column_names
    assert "unique_users" in column_names
    assert "tasks_created" in column_names
    assert "errors" in column_names
    assert "avg_confidence" not in column_names  # Not included in hour grouping

    # Verify data
    assert len(data) == 4
    assert data[0]["hour"] == 0
    assert data[1]["hour"] == 8
    assert data[2]["hour"] == 14
    assert data[3]["hour"] == 20

    # Verify peak hour message is included
    assert message is not None
    assert "Peak Hour: 14:00 with 60 messages" in message


@pytest.mark.integration
def test_telegram_volume_with_user_filter(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume with telegram_user_id filter."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "telegram_user_id": "12345",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 25,
            "unique_users": 1,  # Single user
            "tasks_created": 10,
            "errors": 0,
            "avg_confidence": Decimal("0.92"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes user filter
    call_args = mock_frappe_for_telegram_volume.db.sql.call_args
    query = call_args[0][0]
    params = call_args[0][1]

    assert "AND telegram_user_id = %(telegram_user_id)s" in query
    assert params["telegram_user_id"] == "12345"

    assert len(data) == 1
    assert data[0]["unique_users"] == 1


@pytest.mark.integration
def test_telegram_volume_default_filters(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume with no filters (uses defaults)."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    mock_frappe_for_telegram_volume.db.sql.return_value = []

    columns, data, message, chart = execute(None)

    # Verify default date range (last 7 days)
    call_args = mock_frappe_for_telegram_volume.db.sql.call_args
    params = call_args[0][1]

    # from_date should be 7 days ago
    expected_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    assert params["from_date"] == expected_from

    # to_date should be today
    expected_to = datetime.now().strftime("%Y-%m-%d")
    assert params["to_date"] == expected_to


@pytest.mark.integration
def test_telegram_volume_90_day_limit(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume enforces 90-day limit."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    # Request 120-day range (should throw error)
    filters = {
        "from_date": "2024-10-01",
        "to_date": "2025-01-31",
        "group_by": "Date",
    }

    # Should raise exception via frappe.throw
    with pytest.raises(Exception) as exc_info:
        execute(filters)

    assert "Date range cannot exceed 90 days" in str(exc_info.value)


@pytest.mark.integration
def test_telegram_volume_invalid_date_format(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume handles invalid date format."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    # Invalid date format
    filters = {
        "from_date": "01-01-2025",  # Wrong format
        "to_date": "2025-01-31",
        "group_by": "Date",
    }

    # Should raise exception via frappe.throw
    with pytest.raises(Exception) as exc_info:
        execute(filters)

    assert "Invalid date format" in str(exc_info.value)


@pytest.mark.integration
def test_telegram_volume_cache_behavior(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume uses caching."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    # First call - no cache
    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 100,
            "unique_users": 10,
            "tasks_created": 30,
            "errors": 2,
            "avg_confidence": Decimal("0.88"),
        }
    ]

    cache_mock = mock_frappe_for_telegram_volume.cache.return_value

    columns, data, message, chart = execute(filters)

    # Verify cache was checked
    cache_mock.get.assert_called_once()
    cache_key = cache_mock.get.call_args[0][0]
    assert "telegram_message_volume" in cache_key
    assert "Date" in cache_key
    assert "2025-01-01" in cache_key
    assert "2025-01-07" in cache_key

    # Verify cache was set with 10-minute expiry
    cache_mock.set.assert_called_once()
    assert cache_mock.set.call_args[1]["expires_in_sec"] == 600  # 10 minutes


@pytest.mark.integration
def test_telegram_volume_cache_hit(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume returns cached data when available."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    # Mock cache hit
    cached_data = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 100,
            "unique_users": 10,
            "tasks_created": 30,
            "errors": 2,
            "avg_confidence": Decimal("0.88"),
        }
    ]

    cache_mock = mock_frappe_for_telegram_volume.cache.return_value
    cache_mock.get.return_value = cached_data

    columns, data, message, chart = execute(filters)

    # Verify SQL was NOT called (cache hit)
    mock_frappe_for_telegram_volume.db.sql.assert_not_called()

    # Verify cached data was returned
    assert len(data) == 1
    assert data[0]["total_messages"] == 100


@pytest.mark.integration
def test_telegram_volume_error_handling(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume handles SQL errors gracefully."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    # Mock SQL error
    mock_frappe_for_telegram_volume.db.sql.side_effect = Exception(
        "Database connection error"
    )

    columns, data, message, chart = execute(filters)

    # Verify error was logged
    mock_frappe_for_telegram_volume.log_error.assert_called_once()
    error_message = mock_frappe_for_telegram_volume.log_error.call_args[0][0]
    assert "Error in Telegram Message Volume Report" in error_message

    # Verify empty data returned (graceful degradation)
    assert data == []

    # Verify columns still returned
    assert len(columns) == 6  # Date grouping


@pytest.mark.integration
def test_telegram_volume_peak_hour_calculation(mock_frappe_for_telegram_volume):
    """Test peak hour calculation for Hour grouping."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-07",
        "to_date": "2025-01-07",
        "group_by": "Hour",
    }

    # Mock SQL response with varying message volumes
    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {"hour": 8, "total_messages": 45, "unique_users": 8, "tasks_created": 15, "errors": 1},
        {
            "hour": 14,
            "total_messages": 80,
            "unique_users": 10,
            "tasks_created": 25,
            "errors": 2,
        },  # Peak
        {"hour": 20, "total_messages": 40, "unique_users": 6, "tasks_created": 12, "errors": 0},
    ]

    columns, data, message, chart = execute(filters)

    # Verify peak hour message
    assert message is not None
    assert "Peak Hour: 14:00 with 80 messages" in message


@pytest.mark.integration
def test_telegram_volume_empty_result(mock_frappe_for_telegram_volume):
    """Test Telegram Message Volume with no data."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = []

    columns, data, message, chart = execute(filters)

    # Verify columns returned
    assert len(columns) == 6

    # Verify empty data
    assert len(data) == 0

    # Verify chart handles empty data
    assert chart == {}


@pytest.mark.integration
def test_telegram_volume_chart_structure_date(mock_frappe_for_telegram_volume):
    """Test chart data structure for Date grouping."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 150,
            "unique_users": 12,
            "tasks_created": 45,
            "errors": 3,
            "avg_confidence": Decimal("0.89"),
        },
        {
            "date": date(2025, 1, 6),
            "total_messages": 120,
            "unique_users": 10,
            "tasks_created": 38,
            "errors": 2,
            "avg_confidence": Decimal("0.87"),
        },
    ]

    columns, data, message, chart = execute(filters)

    # Verify chart structure
    assert chart is not None
    assert chart["type"] == "line"
    assert "data" in chart
    assert "labels" in chart["data"]
    assert "datasets" in chart["data"]

    # Verify labels are date strings
    assert len(chart["data"]["labels"]) == 2
    assert chart["data"]["labels"][0] == "2025-01-07"
    assert chart["data"]["labels"][1] == "2025-01-06"

    # Verify values are total_messages
    assert chart["data"]["datasets"][0]["values"][0] == 150
    assert chart["data"]["datasets"][0]["values"][1] == 120


@pytest.mark.integration
def test_telegram_volume_chart_structure_hour(mock_frappe_for_telegram_volume):
    """Test chart data structure for Hour grouping."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-07",
        "to_date": "2025-01-07",
        "group_by": "Hour",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {"hour": 8, "total_messages": 45, "unique_users": 8, "tasks_created": 15, "errors": 1},
        {"hour": 14, "total_messages": 60, "unique_users": 10, "tasks_created": 20, "errors": 2},
    ]

    columns, data, message, chart = execute(filters)

    # Verify chart structure
    assert chart is not None
    assert chart["type"] == "line"

    # Verify labels are hour strings
    assert len(chart["data"]["labels"]) == 2
    assert chart["data"]["labels"][0] == "8"
    assert chart["data"]["labels"][1] == "14"

    # Verify values are total_messages
    assert chart["data"]["datasets"][0]["values"][0] == 45
    assert chart["data"]["datasets"][0]["values"][1] == 60


@pytest.mark.integration
def test_telegram_volume_count_metrics(mock_frappe_for_telegram_volume):
    """Test count metrics (total_messages, unique_users, tasks_created, errors)."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = [
        {
            "date": date(2025, 1, 7),
            "total_messages": 150,
            "unique_users": 12,
            "tasks_created": 45,
            "errors": 3,
            "avg_confidence": Decimal("0.89"),
        }
    ]

    columns, data, message, chart = execute(filters)

    # Verify SQL includes count functions
    call_args = mock_frappe_for_telegram_volume.db.sql.call_args
    query = call_args[0][0]

    assert "COUNT(*) as total_messages" in query
    assert "COUNT(DISTINCT telegram_user_id) as unique_users" in query
    assert "COUNT(created_task_id) as tasks_created" in query
    assert "SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as errors" in query

    # Verify count metrics in data
    assert data[0]["total_messages"] == 150
    assert data[0]["unique_users"] == 12
    assert data[0]["tasks_created"] == 45
    assert data[0]["errors"] == 3


@pytest.mark.integration
def test_telegram_volume_cache_key_includes_user_filter(mock_frappe_for_telegram_volume):
    """Test cache key includes telegram_user_id when provided."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "telegram_user_id": "12345",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = []
    cache_mock = mock_frappe_for_telegram_volume.cache.return_value

    columns, data, message, chart = execute(filters)

    # Verify cache key includes user ID
    cache_key = cache_mock.get.call_args[0][0]
    assert "12345" in cache_key


@pytest.mark.integration
def test_telegram_volume_cache_key_all_users(mock_frappe_for_telegram_volume):
    """Test cache key uses 'all' when no telegram_user_id provided."""
    from flrts_extensions.flrts.report.telegram_message_volume.telegram_message_volume import (
        execute,
    )

    filters = {
        "from_date": "2025-01-01",
        "to_date": "2025-01-07",
        "group_by": "Date",
    }

    mock_frappe_for_telegram_volume.db.sql.return_value = []
    cache_mock = mock_frappe_for_telegram_volume.cache.return_value

    columns, data, message, chart = execute(filters)

    # Verify cache key uses 'all' for all users
    cache_key = cache_mock.get.call_args[0][0]
    assert "all" in cache_key
