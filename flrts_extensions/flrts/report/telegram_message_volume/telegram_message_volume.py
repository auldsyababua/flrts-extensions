from datetime import datetime, timedelta

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data, filters)

    message = None
    if filters.get("group_by") == "Hour":
        peak = calculate_peak_hour(data)
        if peak:
            message = _("Peak Hour: {0}:00 with {1} messages").format(
                peak["hour"], peak["messages"]
            )

    return columns, data, message, chart


def get_columns(filters):
    group_by = filters.get("group_by", "Date")

    if group_by == "Date":
        return [
            {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
            {
                "fieldname": "total_messages",
                "label": _("Total Messages"),
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "fieldname": "unique_users",
                "label": _("Unique Users"),
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "fieldname": "tasks_created",
                "label": _("Tasks Created"),
                "fieldtype": "Int",
                "width": 120,
            },
            {"fieldname": "errors", "label": _("Errors"), "fieldtype": "Int", "width": 120},
            {
                "fieldname": "avg_confidence",
                "label": _("Avg Confidence"),
                "fieldtype": "Float",
                "width": 120,
            },
        ]
    else:  # Hour
        return [
            {"fieldname": "hour", "label": _("Hour"), "fieldtype": "Int", "width": 100},
            {
                "fieldname": "total_messages",
                "label": _("Total Messages"),
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "fieldname": "unique_users",
                "label": _("Unique Users"),
                "fieldtype": "Int",
                "width": 120,
            },
            {
                "fieldname": "tasks_created",
                "label": _("Tasks Created"),
                "fieldtype": "Int",
                "width": 120,
            },
            {"fieldname": "errors", "label": _("Errors"), "fieldtype": "Int", "width": 120},
        ]


def get_data(filters):
    # Server-side filter defaults
    group_by = filters.get("group_by", "Date")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    telegram_user_id = filters.get("telegram_user_id")

    # Apply defaults if not provided
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")

    # Limit to 90 days
    try:
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")
        if (end - start).days > 90:
            frappe.throw(_("Date range cannot exceed 90 days"))
    except ValueError:
        frappe.throw(_("Invalid date format"))

    # Cache key
    cache_key = (
        f"telegram_message_volume_{group_by}_{from_date}_{to_date}_{telegram_user_id or 'all'}"
    )
    cached_data = frappe.cache().get(cache_key)
    if cached_data:
        return cached_data

    conditions = "creation >= %(from_date)s AND creation <= %(to_date)s"
    params = {"from_date": from_date, "to_date": to_date}

    if telegram_user_id:
        conditions += " AND telegram_user_id = %(telegram_user_id)s"
        params["telegram_user_id"] = telegram_user_id

    if group_by == "Date":
        query = f"""
        SELECT
            DATE(creation) as date,
            COUNT(*) as total_messages,
            COUNT(DISTINCT telegram_user_id) as unique_users,
            COUNT(created_task_id) as tasks_created,
            SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as errors,
            ROUND(AVG(confidence_score), 2) as avg_confidence
        FROM `tabFLRTS Parser Log`
        WHERE {conditions}
        GROUP BY DATE(creation)
        ORDER BY date DESC
        """
    else:
        query = f"""
        SELECT
            HOUR(creation) as hour,
            COUNT(*) as total_messages,
            COUNT(DISTINCT telegram_user_id) as unique_users,
            COUNT(created_task_id) as tasks_created,
            SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as errors
        FROM `tabFLRTS Parser Log`
        WHERE {conditions}
        GROUP BY HOUR(creation)
        ORDER BY hour
        """

    try:
        data = frappe.db.sql(query, params, as_dict=True)
        frappe.cache().set(cache_key, data, expires_in_sec=600)
        return data
    except Exception as e:
        frappe.log_error(f"Error in Telegram Message Volume Report: {str(e)}")
        return []


def get_chart_data(data, filters):
    group_by = filters.get("group_by", "Date")

    if not data:
        return {}

    labels = []
    values = []

    for row in data:
        if group_by == "Date":
            labels.append(str(row["date"]))
        else:
            labels.append(str(row["hour"]))
        values.append(row["total_messages"])

    return {
        "data": {"labels": labels, "datasets": [{"name": _("Total Messages"), "values": values}]},
        "type": "line",
        "colors": ["#3498db"],
    }


def calculate_peak_hour(data):
    if not data:
        return None

    max_messages = 0
    peak_hour = None

    for row in data:
        if row["total_messages"] > max_messages:
            max_messages = row["total_messages"]
            peak_hour = row["hour"]

    return {"hour": peak_hour, "messages": max_messages}
