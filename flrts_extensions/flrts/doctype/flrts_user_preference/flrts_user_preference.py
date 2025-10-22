from datetime import datetime
from zoneinfo import available_timezones

import frappe
from frappe.model.document import Document


class FLRTSUserPreference(Document):
    def validate(self):
        # Validate Telegram user ID uniqueness
        if self.telegram_user_id:
            existing = frappe.db.exists(
                "FLRTS User Preference",
                {"telegram_user_id": self.telegram_user_id, "name": ["!=", self.name]},
            )
            if existing:
                frappe.throw(
                    f"Telegram user ID {self.telegram_user_id} is already linked to another user"
                )

        # Validate quiet hours
        if self.notification_quiet_hours_start and self.notification_quiet_hours_end:
            start = datetime.strptime(self.notification_quiet_hours_start, "%H:%M:%S")
            end = datetime.strptime(self.notification_quiet_hours_end, "%H:%M:%S")
            if end <= start:
                frappe.throw("Quiet hours end time must be after start time")

        # Validate timezone
        if self.timezone:
            if self.timezone not in available_timezones():
                frappe.throw(f"Invalid timezone: {self.timezone}. Must be a valid IANA timezone.")


def get_permission_query_conditions(user):
    """Restrict access to own records only (unless Administrator)."""
    if not user:
        user = frappe.session.user

    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return None

    return f"`tabFLRTS User Preference`.user = {frappe.db.escape(user)}"


def has_permission(doc, ptype, user):
    """Allow access only to own records (unless Administrator)."""
    if not user:
        user = frappe.session.user

    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return True

    return doc.user == user
