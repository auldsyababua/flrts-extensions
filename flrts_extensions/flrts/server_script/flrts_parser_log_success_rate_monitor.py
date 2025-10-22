import frappe
from frappe.utils import add_days, get_url, now


def execute():
    """
    Scheduled Server Script to monitor FLRTS Parser Log success rate.
    Runs daily at 9 AM, sends email alert if success rate drops below threshold.
    """
    try:
        # Get threshold from System Settings with validation (default 80.0)
        threshold_value = frappe.db.get_single_value(
            "System Settings", "custom_flrts_success_rate_threshold"
        )
        try:
            threshold = float(threshold_value) if threshold_value is not None else 80.0
            # Clamp to valid range [0.0, 100.0]
            if threshold < 0.0:
                frappe.logger().warning(
                    f"FLRTS Success Rate Monitor: Invalid threshold {threshold}, clamping to 0.0"
                )
                threshold = 0.0
            elif threshold > 100.0:
                frappe.logger().warning(
                    f"FLRTS Success Rate Monitor: Invalid threshold {threshold}, clamping to 100.0"
                )
                threshold = 100.0
        except (ValueError, TypeError) as e:
            frappe.logger().warning(
                f"FLRTS Success Rate Monitor: Invalid threshold value '{threshold_value}', using default 80.0: {str(e)}"
            )
            threshold = 80.0

        # Get logs from last 24 hours
        yesterday = add_days(now(), -1)
        logs = frappe.db.get_all(
            "FLRTS Parser Log", filters={"creation": [">=", yesterday]}, fields=["user_accepted"]
        )

        total_parses = len(logs)
        accepted = sum(1 for log in logs if log.user_accepted == "Accepted")
        rejected = sum(1 for log in logs if log.user_accepted == "Rejected")
        pending = sum(1 for log in logs if log.user_accepted == "Pending")

        # Skip if no completed parses (guard against division by zero)
        if accepted + rejected == 0:
            frappe.logger().info(
                "FLRTS Success Rate Monitor: No completed parses in last 24 hours, skipping alert"
            )
            return

        success_rate = (accepted / (accepted + rejected)) * 100
        alert_sent = False

        if success_rate < threshold:
            # Prepare email
            subject = f"🚨 FLRTS Parser Success Rate Alert: {success_rate:.1f}%"
            body = f"""
FLRTS Parser Success Rate Alert

Current Success Rate: {success_rate:.1f}% (Threshold: {threshold}%)

Last 24 Hours:
- Total Parses: {total_parses}
- Accepted: {accepted}
- Rejected: {rejected}
- Pending: {pending}

Links:
- FLRTS Parser Log: {get_url("/app/flrts-parser-log")}
- Parser Performance Report: {get_url("/app/query-report/parser-performance-dashboard")}

Suggested Actions:
1. Review failed parses in the Parser Log
2. Analyze rejection patterns
3. Update OpenAI prompts if needed
4. Check for context data issues (users/sites)

This is an automated alert from FLRTS monitoring.
"""

            # Get recipients - try custom emails first, then System Managers
            custom_emails = frappe.db.get_single_value(
                "System Settings", "custom_flrts_alert_emails"
            )
            if custom_emails:
                recipients = [email.strip() for email in custom_emails.split(",") if email.strip()]
            else:
                # Fallback to System Managers
                # Get user IDs with System Manager role
                system_manager_ids = frappe.get_all(
                    "Has Role", filters={"role": "System Manager"}, pluck="parent"
                )
                # Get emails from User where enabled
                if system_manager_ids:
                    recipients = frappe.get_all(
                        "User",
                        filters={"name": ["in", system_manager_ids], "enabled": 1},
                        pluck="email",
                    )
                else:
                    recipients = []

            # Guard against empty recipients
            if not recipients:
                frappe.logger().warning(
                    "FLRTS Success Rate Monitor: No recipients found, skipping alert email"
                )
                return

            # Send email
            frappe.sendmail(recipients=recipients, subject=subject, message=body)
            alert_sent = True

        # Log monitoring activity
        frappe.logger().info(
            f"FLRTS Success Rate Monitor: success_rate={success_rate:.1f}%, threshold={threshold}%, alert_sent={alert_sent}"
        )

    except Exception as e:
        error_msg = f"Error in FLRTS Success Rate Monitor: {str(e)}"
        frappe.log_error(error_msg)

        # Send fallback error email using resolved recipients
        try:
            # Get recipients using same logic
            custom_emails = frappe.db.get_single_value(
                "System Settings", "custom_flrts_alert_emails"
            )
            if custom_emails:
                error_recipients = [
                    email.strip() for email in custom_emails.split(",") if email.strip()
                ]
            else:
                system_manager_ids = frappe.get_all(
                    "Has Role", filters={"role": "System Manager"}, pluck="parent"
                )
                if system_manager_ids:
                    error_recipients = frappe.get_all(
                        "User",
                        filters={"name": ["in", system_manager_ids], "enabled": 1},
                        pluck="email",
                    )
                else:
                    error_recipients = []

            if error_recipients:
                frappe.sendmail(
                    recipients=error_recipients,
                    subject="🚨 FLRTS Success Rate Monitor Error",
                    message=f"Error in monitoring script:\n\n{error_msg}\n\nPlease check the Error Log for details.",
                )
        except Exception:
            # If even fallback email fails, just log
            pass
