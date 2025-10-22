import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Min, Sum
from frappe.utils import get_last_day, getdate
from pypika import CustomFunction


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    summary = get_summary_row(data)
    chart = get_chart_data(data, filters)

    # Append summary row to data instead of returning as 5th value
    if summary:
        data.extend(summary)

    return columns, data, None, chart


def get_columns():
    return [
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {
            "fieldname": "total_requests",
            "label": _("Total Requests"),
            "fieldtype": "Int",
            "width": 120,
        },
        {"fieldname": "total_tokens", "label": _("Total Tokens"), "fieldtype": "Int", "width": 120},
        {
            "fieldname": "prompt_tokens",
            "label": _("Prompt Tokens"),
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "fieldname": "completion_tokens",
            "label": _("Completion Tokens"),
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "fieldname": "total_cost",
            "label": _("Total Cost"),
            "fieldtype": "Currency",
            "width": 100,
            "options": "USD",
        },
        {
            "fieldname": "avg_cost_per_request",
            "label": _("Avg Cost per Request"),
            "fieldtype": "Currency",
            "width": 140,
            "options": "USD",
        },
        {"fieldname": "model_name", "label": _("Model Name"), "fieldtype": "Data", "width": 120},
        {
            "fieldname": "projected_monthly_cost",
            "label": _("Projected Monthly Cost"),
            "fieldtype": "Currency",
            "width": 150,
            "options": "USD",
        },
        {
            "fieldname": "budget_status",
            "label": _("Budget Status"),
            "fieldtype": "Data",
            "width": 120,
            "indicator": "green",
        },
    ]


def get_data(filters):
    if not filters:
        filters = {}

    # Server-side filter defaults
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    model_name = filters.get("model_name")
    group_by = filters.get("group_by", "Date")

    if not from_date:
        # First day of current month
        from_date = getdate().replace(day=1)
    if not to_date:
        to_date = getdate()

    # Define DocType and custom functions
    ParserLog = DocType("FLRTS Parser Log")
    DATE = CustomFunction("DATE", ["date_field"])
    ROUND = CustomFunction("ROUND", ["value", "decimals"])

    # Build base query
    # Use aggregated date when grouping by model to satisfy ONLY_FULL_GROUP_BY
    date_expr = (
        Min(DATE(ParserLog.creation)).as_("date")
        if group_by == "Model Name"
        else DATE(ParserLog.creation).as_("date")
    )

    query = (
        frappe.qb.from_(ParserLog)
        .select(
            date_expr,
            Count("*").as_("total_requests"),
            Sum(ParserLog.total_tokens).as_("total_tokens"),
            Sum(ParserLog.prompt_tokens).as_("prompt_tokens"),
            Sum(ParserLog.completion_tokens).as_("completion_tokens"),
            ROUND(Sum(ParserLog.estimated_cost_usd), 4).as_("total_cost"),
            ROUND(Sum(ParserLog.estimated_cost_usd) / Count("*"), 6).as_("avg_cost_per_request"),
            ParserLog.model_name,
        )
        .where(ParserLog.creation >= from_date)
        .where(ParserLog.creation <= to_date)
    )

    # Add optional model filter
    if model_name:
        query = query.where(ParserLog.model_name == model_name)

    # Group by logic based on filter
    if group_by == "Model Name":
        query = query.groupby(ParserLog.model_name)
    else:
        if model_name:
            query = query.groupby(DATE(ParserLog.creation), ParserLog.model_name)
        else:
            query = query.groupby(DATE(ParserLog.creation))

    # Order by
    if group_by == "Model Name":
        query = query.orderby(ParserLog.model_name)
    else:
        query = query.orderby(DATE(ParserLog.creation), order=frappe.qb.desc)

    # Execute query
    data = query.run(as_dict=True)

    # Calculate projected monthly cost
    current_day = getdate().day
    days_in_month = get_last_day(getdate()).day

    for row in data:
        if row.total_cost:
            row.projected_monthly_cost = round((row.total_cost / current_day) * days_in_month, 4)
        else:
            row.projected_monthly_cost = 0

        # Budget status indicator
        if row.total_cost and row.total_cost >= 10:
            row.budget_status = "⚠️ Over Budget"
            row["indicator"] = "red"
        else:
            row.budget_status = "✅ Under Budget"
            row["indicator"] = "green"

    return data


def get_summary_row(data):
    if not data:
        return []

    total_requests = sum(row.total_requests for row in data)
    total_tokens = sum(row.total_tokens for row in data)
    prompt_tokens = sum(row.prompt_tokens for row in data)
    completion_tokens = sum(row.completion_tokens for row in data)
    total_cost = sum(row.total_cost for row in data)
    avg_cost_per_request = round(total_cost / total_requests, 6) if total_requests else 0
    projected_monthly_cost = sum(row.projected_monthly_cost for row in data)

    # Return total row with date = 'Total' and blank model_name
    return [
        {
            "date": "Total",
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost": round(total_cost, 4),
            "avg_cost_per_request": avg_cost_per_request,
            "model_name": "",
            "projected_monthly_cost": round(projected_monthly_cost, 4),
            "budget_status": "",
        }
    ]


def get_chart_data(data, filters):
    if not data:
        return None

    # Exclude summary row from chart
    rows = [r for r in data if str(r.get("date")) != "Total"]
    dates = [str(r.get("date")) for r in rows]
    costs = [r.get("total_cost", 0) for r in rows]
    colors = ["#28a745" if cost < 10 else "#dc3545" for cost in costs]

    return {
        "data": {"labels": dates, "datasets": [{"name": "Total Cost", "values": costs}]},
        "type": "bar",
        "colors": colors,
        "barOptions": {"spaceRatio": 0.5},
    }
