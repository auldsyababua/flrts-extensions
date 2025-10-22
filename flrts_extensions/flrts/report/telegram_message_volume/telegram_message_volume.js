frappe.query_reports['Telegram Message Volume'] = {
	filters: [
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -7),
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
			fieldname: 'group_by',
			label: __('Group By'),
			fieldtype: 'Select',
			options: ['Date', 'Hour'],
			default: 'Date',
			reqd: 1
		},
		{
			fieldname: 'telegram_user_id',
			label: __('Telegram User ID'),
			fieldtype: 'Data',
			reqd: 0
		}
	]
};
