# -*- coding: utf-8 -*-
"""Installation and setup for FLRTS Extensions."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_custom_fields():
    """Install custom fields on Maintenance Visit DocType."""
    custom_fields = {
        "Maintenance Visit": [
            {
                "fieldname": "supabase_task_id",
                "fieldtype": "Data",
                "label": "Supabase Task ID",
                "insert_after": "name",
                "unique": 1,
                "read_only": 1,
                "description": "Original Supabase task UUID (for future reconciliation and audit)",
            },
            {
                "fieldname": "flrts_owner",
                "fieldtype": "Link",
                "options": "User",
                "label": "FLRTS Owner",
                "insert_after": "supabase_task_id",
                "description": "Internal task owner (FLRTS personnel who owns this task)",
            },
            {
                "fieldname": "flrts_priority",
                "fieldtype": "Select",
                "options": "1\n2\n3\n4\n5",
                "label": "Priority",
                "insert_after": "flrts_owner",
                "default": "3",
                "description": "Task priority (1=Urgent, 2=High, 3=Normal, 4=Low, 5=Lowest)",
            },
            {
                "fieldname": "flrts_site",
                "fieldtype": "Link",
                "options": "Mining Site",
                "label": "Mining Site",
                "insert_after": "flrts_priority",
                "description": "Mining site where maintenance was performed",
            },
            {
                "fieldname": "flrts_contractor",
                "fieldtype": "Link",
                "options": "Contractor",
                "label": "Contractor",
                "insert_after": "flrts_site",
                "description": "Contractor responsible for maintenance work",
            },
            {
                "fieldname": "flrts_metadata",
                "fieldtype": "JSON",
                "label": "Metadata",
                "insert_after": "flrts_contractor",
                "description": "Custom metadata in JSON format (for integrations and extensions)",
            },
            {
                "fieldname": "custom_synced_at",
                "fieldtype": "Datetime",
                "label": "Last Synced (Supabase)",
                "insert_after": "flrts_metadata",
                "read_only": 1,
                "description": "Timestamp of last sync from Supabase (migration artifact)",
            },
        ]
    }

    create_custom_fields(custom_fields)
    frappe.db.commit()
    print("✅ Custom fields installed successfully on Maintenance Visit DocType")
