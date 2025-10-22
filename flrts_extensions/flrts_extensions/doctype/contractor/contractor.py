# -*- coding: utf-8 -*-
"""Contractor DocType controller."""

from frappe.model.document import Document


class Contractor(Document):
    """Contractor document controller."""

    def validate(self):
        """Validate Contractor before saving."""
        # Future: Add custom validation logic here
        pass
