import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count, Sum
from frappe.utils import add_days, getdate
from pypika import CustomFunction
from pypika.terms import Case


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart


def get_columns():
    return [
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "total_parses", "label": _("Total Parses"), "fieldtype": "Int", "width": 120},
        {"fieldname": "accepted", "label": _("Accepted"), "fieldtype": "Int", "width": 100},
        {"fieldname": "rejected", "label": _("Rejected"), "fieldtype": "Int", "width": 100},
        {"fieldname": "pending", "label": _("Pending"), "fieldtype": "Int", "width": 100},
        {
            "fieldname": "success_rate",
            "label": _("Success Rate (%)"),
            "fieldtype": "Percent",
            "width": 130,
        },
        {
            "fieldname": "avg_confidence",
            "label": _("Avg Confidence"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "avg_response_ms",
            "label": _("Avg Response (ms)"),
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "avg_erpnext_response_ms",
            "label": _("Avg ERPNext API (ms)"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "total_cost",
            "label": _("Total Cost ($)"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "avg_cost_per_parse",
            "label": _("Avg Cost per Parse ($)"),
            "fieldtype": "Currency",
            "width": 160,
        },
    ]


def get_data(filters):
    if not filters:
        filters = {}

    # Server-side filter defaults
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    telegram_user_id = filters.get("telegram_user_id")
    model_name = filters.get("model_name")

    if not from_date:
        from_date = add_days(getdate(), -30)
    if not to_date:
        to_date = getdate()

    # Limit to 90 days for performance
    if (getdate(to_date) - getdate(from_date)).days > 90:
        from_date = add_days(getdate(to_date), -90)

    # Check cache
    cache_key = f"parser_performance_dashboard_{from_date}_{to_date}"
    cached_data = frappe.cache().get_value(cache_key)
    if cached_data:
        return cached_data

    # Define DocType and custom functions
    ParserLog = DocType("FLRTS Parser Log")
    DATE = CustomFunction("DATE", ["date_field"])
    ROUND = CustomFunction("ROUND", ["value", "decimals"])
    NULLIF = CustomFunction("NULLIF", ["value1", "value2"])

    try:
        # Define CASE expressions for user_accepted status
        accepted_case = Case().when(ParserLog.user_accepted == "Accepted", 1).else_(0)
        rejected_case = Case().when(ParserLog.user_accepted == "Rejected", 1).else_(0)
        pending_case = Case().when(ParserLog.user_accepted == "Pending", 1).else_(0)

        # Calculate accepted and rejected sums for success rate
        accepted_sum = Sum(accepted_case)
        rejected_sum = Sum(rejected_case)
        total_reviewed = accepted_sum + rejected_sum

        # Success rate calculation: avoid division by zero
        success_rate = Case().when(
            total_reviewed > 0, ROUND((accepted_sum * 100.0) / total_reviewed, 2)
        ).else_(0)

        # Build query
        query = (
            frappe.qb.from_(ParserLog)
            .select(
                DATE(ParserLog.creation).as_("date"),
                Count("*").as_("total_parses"),
                accepted_sum.as_("accepted"),
                rejected_sum.as_("rejected"),
                Sum(pending_case).as_("pending"),
                success_rate.as_("success_rate"),
                ROUND(Avg(ParserLog.confidence_score), 2).as_("avg_confidence"),
                ROUND(Avg(ParserLog.response_duration_ms), 0).as_("avg_response_ms"),
                ROUND(Avg(ParserLog.erpnext_response_ms), 0).as_("avg_erpnext_response_ms"),
                ROUND(Sum(ParserLog.estimated_cost_usd), 4).as_("total_cost"),
                ROUND(Sum(ParserLog.estimated_cost_usd) / NULLIF(Count("*"), 0), 4).as_(
                    "avg_cost_per_parse"
                ),
            )
            .where(ParserLog.creation >= from_date)
            .where(ParserLog.creation <= to_date)
        )

        # Add optional filters
        if telegram_user_id:
            query = query.where(ParserLog.telegram_user_id == telegram_user_id)

        if model_name:
            query = query.where(ParserLog.model_name == model_name)

        # Group by and order
        query = query.groupby(DATE(ParserLog.creation))
        query = query.orderby(DATE(ParserLog.creation), order=frappe.qb.desc)

        # Execute query
        data = query.run(as_dict=True)

        # Cache for 5 minutes
        frappe.cache().set_value(cache_key, data, expires_in_sec=300)

        return data

    except Exception as e:
        frappe.log_error(f"Error in Parser Performance Dashboard: {str(e)}")
        return []


def get_chart_data(data):
    if not data:
        return None

    labels = [str(row.get("date")) for row in data]
    success_rates = [row.get("success_rate", 0) for row in data]

    # Single-axis chart showing success rate only
    # Cost data is available in the table columns
    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Success Rate (%)", "values": success_rates}],
        },
        "type": "line",
        "colors": ["#28a745"],
        "axisOptions": {"xAxisMode": "tick", "xIsSeries": True},
        "lineOptions": {"regionFill": 1, "hideDots": 0},
    }
