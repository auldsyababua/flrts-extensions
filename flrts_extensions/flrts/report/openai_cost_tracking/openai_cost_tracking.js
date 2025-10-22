frappe.query_reports['OpenAI Cost Tracking'] = {
	filters: [
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.month_start(),
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
			fieldname: 'model_name',
			label: __('Model Name'),
			fieldtype: 'Data',
			reqd: 0
		},
		{
			fieldname: 'group_by',
			label: __('Group By'),
			fieldtype: 'Select',
			options: ['Date', 'Model Name'],
			default: 'Date',
			reqd: 1
		}
	]
};
