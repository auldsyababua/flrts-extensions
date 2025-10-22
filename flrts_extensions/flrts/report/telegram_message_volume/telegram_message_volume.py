from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Sum
from pypika import CustomFunction
from pypika.terms import Case


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

    # Define DocType and custom functions
    ParserLog = DocType("FLRTS Parser Log")
    DATE = CustomFunction("DATE", ["date_field"])
    HOUR = CustomFunction("HOUR", ["date_field"])
    ROUND = CustomFunction("ROUND", ["value", "decimals"])
    COUNT_DISTINCT = CustomFunction("COUNT", ["DISTINCT", "field"])

    # Define CASE expression for errors
    error_case = Case().when(ParserLog.error_occurred == 1, 1).else_(0)

    try:
        if group_by == "Date":
            # Query 1: Group by Date
            query = (
                frappe.qb.from_(ParserLog)
                .select(
                    DATE(ParserLog.creation).as_("date"),
                    Count("*").as_("total_messages"),
                    COUNT_DISTINCT("DISTINCT", ParserLog.telegram_user_id).as_("unique_users"),
                    Count(ParserLog.created_task_id).as_("tasks_created"),
                    Sum(error_case).as_("errors"),
                    ROUND(Avg(ParserLog.confidence_score), 2).as_("avg_confidence"),
                )
                .where(ParserLog.creation >= from_date)
                .where(ParserLog.creation <= to_date)
            )

            # Add optional user filter
            if telegram_user_id:
                query = query.where(ParserLog.telegram_user_id == telegram_user_id)

            # Group by and order
            query = query.groupby(DATE(ParserLog.creation))
            query = query.orderby(DATE(ParserLog.creation), order=frappe.qb.desc)

        else:
            # Query 2: Group by Hour
            query = (
                frappe.qb.from_(ParserLog)
                .select(
                    HOUR(ParserLog.creation).as_("hour"),
                    Count("*").as_("total_messages"),
                    COUNT_DISTINCT("DISTINCT", ParserLog.telegram_user_id).as_("unique_users"),
                    Count(ParserLog.created_task_id).as_("tasks_created"),
                    Sum(error_case).as_("errors"),
                )
                .where(ParserLog.creation >= from_date)
                .where(ParserLog.creation <= to_date)
            )

            # Add optional user filter
            if telegram_user_id:
                query = query.where(ParserLog.telegram_user_id == telegram_user_id)

            # Group by and order
            query = query.groupby(HOUR(ParserLog.creation))
            query = query.orderby(HOUR(ParserLog.creation))

        # Execute query
        data = query.run(as_dict=True)
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
