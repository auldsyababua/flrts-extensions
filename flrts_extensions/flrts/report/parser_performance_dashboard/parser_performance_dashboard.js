frappe.query_reports['Parser Performance Dashboard'] = {
	filters: [
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
			reqd: 1
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: 'telegram_user_id',
			label: __('Telegram User ID'),
			fieldtype: 'Data',
			reqd: 0
		},
		{
			fieldname: 'model_name',
			label: __('Model Name'),
			fieldtype: 'Data',
			reqd: 0
		}
	]
};
