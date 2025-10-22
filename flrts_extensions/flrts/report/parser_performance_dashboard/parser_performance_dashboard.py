import frappe
from frappe import _
from frappe.utils import getdate, add_days, now_datetime
import datetime

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "total_parses",
			"label": _("Total Parses"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "accepted",
			"label": _("Accepted"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "rejected",
			"label": _("Rejected"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "pending",
			"label": _("Pending"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "success_rate",
			"label": _("Success Rate (%)"),
			"fieldtype": "Percent",
			"width": 130
		},
		{
			"fieldname": "avg_confidence",
			"label": _("Avg Confidence"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "avg_response_ms",
			"label": _("Avg Response (ms)"),
			"fieldtype": "Int",
			"width": 140
		},
		{
			"fieldname": "avg_erpnext_response_ms",
			"label": _("Avg ERPNext API (ms)"),
			"fieldtype": "Int",
			"width": 150
		},
		{
			"fieldname": "total_cost",
			"label": _("Total Cost ($)"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "avg_cost_per_parse",
			"label": _("Avg Cost per Parse ($)"),
			"fieldtype": "Currency",
			"width": 160
		}
	]

def get_data(filters):
	if not filters:
		filters = {}

	# Server-side filter defaults
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	telegram_user_id = filters.get('telegram_user_id')
	model_name = filters.get('model_name')

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

	# Build conditions
	conditions = "creation >= %(from_date)s AND creation <= %(to_date)s"
	params = {"from_date": from_date, "to_date": to_date}

	if telegram_user_id:
		conditions += " AND telegram_user_id = %(telegram_user_id)s"
		params["telegram_user_id"] = telegram_user_id

	if model_name:
		conditions += " AND model_name = %(model_name)s"
		params["model_name"] = model_name

	try:
		query = f"""
			SELECT
				DATE(creation) as date,
				COUNT(*) as total_parses,
				SUM(CASE WHEN user_accepted = 'Accepted' THEN 1 ELSE 0 END) as accepted,
				SUM(CASE WHEN user_accepted = 'Rejected' THEN 1 ELSE 0 END) as rejected,
				SUM(CASE WHEN user_accepted = 'Pending' THEN 1 ELSE 0 END) as pending,
				CASE
					WHEN (SUM(CASE WHEN user_accepted = 'Accepted' THEN 1 ELSE 0 END) + SUM(CASE WHEN user_accepted = 'Rejected' THEN 1 ELSE 0 END)) > 0
					THEN ROUND((SUM(CASE WHEN user_accepted = 'Accepted' THEN 1 ELSE 0 END) * 100.0) / (SUM(CASE WHEN user_accepted = 'Accepted' THEN 1 ELSE 0 END) + SUM(CASE WHEN user_accepted = 'Rejected' THEN 1 ELSE 0 END)), 2)
					ELSE 0
				END as success_rate,
				ROUND(AVG(confidence_score), 2) as avg_confidence,
				ROUND(AVG(response_duration_ms)) as avg_response_ms,
				ROUND(AVG(erpnext_response_ms)) as avg_erpnext_response_ms,
				ROUND(SUM(estimated_cost_usd), 4) as total_cost,
				ROUND(SUM(estimated_cost_usd) / NULLIF(COUNT(*), 0), 4) as avg_cost_per_parse
			FROM `tabFLRTS Parser Log`
			WHERE {conditions}
			GROUP BY DATE(creation)
			ORDER BY date DESC
		"""

		data = frappe.db.sql(query, params, as_dict=True)

		# Cache for 5 minutes
		frappe.cache().set_value(cache_key, data, expires_in_sec=300)

		return data

	except Exception as e:
		frappe.log_error(f"Error in Parser Performance Dashboard: {str(e)}")
		return []

def get_chart_data(data):
	if not data:
		return None

	labels = [str(row.get('date')) for row in data]
	success_rates = [row.get('success_rate', 0) for row in data]

	# Single-axis chart showing success rate only
	# Cost data is available in the table columns
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Success Rate (%)",
					"values": success_rates
				}
			]
		},
		"type": "line",
		"colors": ["#28a745"],
		"axisOptions": {
			"xAxisMode": "tick",
			"xIsSeries": True
		},
		"lineOptions": {
			"regionFill": 1,
			"hideDots": 0
		}
	}