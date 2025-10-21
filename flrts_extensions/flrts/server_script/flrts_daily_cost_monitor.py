import frappe
import datetime
import calendar

def execute():
    try:
        # Get today's date
        today = datetime.date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # Query today's costs and parses
        query = """
            SELECT 
                SUM(estimated_cost_usd) as total_cost,
                COUNT(*) as total_parses
            FROM `tabFLRTS Parser Log`
            WHERE DATE(creation) = %s
        """
        result = frappe.db.sql(query, (today_str,), as_dict=True)
        
        total_cost = result[0].get('total_cost') or 0.0
        total_parses = result[0].get('total_parses') or 0
        
        # Calculate projected monthly cost (guard against division by zero)
        current_day = today.day
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        if current_day > 0 and total_cost > 0:
            projected_monthly = (total_cost / current_day) * days_in_month
        else:
            projected_monthly = 0.0
        
        # Calculate average cost per parse (guard against division by zero)
        avg_cost_per_parse = total_cost / total_parses if total_parses > 0 else 0.0
        
        # Get thresholds from System Settings with validation
        daily_threshold_value = frappe.db.get_single_value('System Settings', 'custom_flrts_daily_cost_threshold')
        monthly_threshold_value = frappe.db.get_single_value('System Settings', 'custom_flrts_monthly_cost_threshold')

        # Validate daily threshold
        try:
            daily_threshold = float(daily_threshold_value) if daily_threshold_value is not None else 10.00
            # Clamp to valid range [0.0, +inf)
            if daily_threshold < 0.0:
                frappe.logger().warning(f"FLRTS Daily Cost Monitor: Invalid daily threshold {daily_threshold}, clamping to 0.0")
                daily_threshold = 0.0
        except (ValueError, TypeError) as e:
            frappe.logger().warning(f"FLRTS Daily Cost Monitor: Invalid daily threshold value '{daily_threshold_value}', using default 10.00: {str(e)}")
            daily_threshold = 10.00

        # Validate monthly threshold
        try:
            monthly_threshold = float(monthly_threshold_value) if monthly_threshold_value is not None else 300.00
            # Clamp to valid range [0.0, +inf)
            if monthly_threshold < 0.0:
                frappe.logger().warning(f"FLRTS Daily Cost Monitor: Invalid monthly threshold {monthly_threshold}, clamping to 0.0")
                monthly_threshold = 0.0
        except (ValueError, TypeError) as e:
            frappe.logger().warning(f"FLRTS Daily Cost Monitor: Invalid monthly threshold value '{monthly_threshold_value}', using default 300.00: {str(e)}")
            monthly_threshold = 300.00

        # Get recipients with fallback chain
        cost_alert_emails = frappe.db.get_single_value('System Settings', 'custom_flrts_cost_alert_emails')
        if cost_alert_emails:
            alert_emails = [email.strip() for email in cost_alert_emails.split(',') if email.strip()]
        else:
            # Fallback to custom_flrts_alert_emails
            general_alert_emails = frappe.db.get_single_value('System Settings', 'custom_flrts_alert_emails')
            if general_alert_emails:
                alert_emails = [email.strip() for email in general_alert_emails.split(',') if email.strip()]
            else:
                # Final fallback to System Managers
                system_manager_ids = frappe.get_all('Has Role',
                    filters={'role': 'System Manager'},
                    pluck='parent'
                )
                if system_manager_ids:
                    alert_emails = frappe.get_all('User',
                        filters={'name': ['in', system_manager_ids], 'enabled': 1},
                        pluck='email'
                    )
                else:
                    alert_emails = []

        # Guard against empty recipients
        if not alert_emails:
            frappe.logger().warning("FLRTS Daily Cost Monitor: No recipients found, skipping alert email")
            return
        
        # Check if alert needed
        alert_needed = total_cost > daily_threshold or projected_monthly > monthly_threshold
        
        if alert_needed:
            # Prepare email
            subject = f"💰 FLRTS OpenAI Cost Alert: ${total_cost:.2f} today"
            
            cost_tracking_url = frappe.utils.get_url('/app/query-report/OpenAI Cost Tracking')
            
            message = f"""
            <h3>FLRTS OpenAI Cost Alert</h3>
            
            <p><strong>Today's Total Cost:</strong> ${total_cost:.2f}</p>
            <p><strong>Projected Monthly Cost:</strong> ${projected_monthly:.2f}</p>
            <p><strong>Daily Threshold:</strong> ${daily_threshold:.2f}</p>
            <p><strong>Monthly Threshold:</strong> ${monthly_threshold:.2f}</p>
            
            <p><strong>Total Parses Today:</strong> {total_parses}</p>
            <p><strong>Average Cost per Parse:</strong> ${avg_cost_per_parse:.4f}</p>
            
            <p><a href="{cost_tracking_url}">View Cost Tracking Report</a></p>
            
            <h4>Suggested Actions:</h4>
            <ul>
                <li>Review high-cost parses in the Cost Tracking Report</li>
                <li>Optimize OpenAI prompts to reduce token usage</li>
                <li>Consider using gpt-4o-mini for non-critical parses</li>
                <li>Check for retry loops or excessive API calls</li>
            </ul>
            
            <p>This is an automated alert from FLRTS monitoring.</p>
            """
            
            # Send email
            frappe.sendmail(
                recipients=alert_emails,
                subject=subject,
                message=message
            )
            
            frappe.logger().info(f"Cost alert sent: ${total_cost:.2f} today, projected ${projected_monthly:.2f} monthly")
        else:
            frappe.logger().info(f"Cost monitoring: ${total_cost:.2f} today, projected ${projected_monthly:.2f} monthly - no alert needed")
            
    except Exception as e:
        frappe.logger().error(f"Error in daily cost monitor: {str(e)}")

        # Send error notification using fallback chain
        try:
            cost_alert_emails = frappe.db.get_single_value('System Settings', 'custom_flrts_cost_alert_emails')
            if cost_alert_emails:
                error_recipients = [email.strip() for email in cost_alert_emails.split(',') if email.strip()]
            else:
                general_alert_emails = frappe.db.get_single_value('System Settings', 'custom_flrts_alert_emails')
                if general_alert_emails:
                    error_recipients = [email.strip() for email in general_alert_emails.split(',') if email.strip()]
                else:
                    system_manager_ids = frappe.get_all('Has Role',
                        filters={'role': 'System Manager'},
                        pluck='parent'
                    )
                    if system_manager_ids:
                        error_recipients = frappe.get_all('User',
                            filters={'name': ['in', system_manager_ids], 'enabled': 1},
                            pluck='email'
                        )
                    else:
                        error_recipients = []

            if error_recipients:
                frappe.sendmail(
                    recipients=error_recipients,
                    subject="🚨 FLRTS Daily Cost Monitor Error",
                    message=f"Error in daily cost monitoring script: {str(e)}"
                )
        except:
            pass