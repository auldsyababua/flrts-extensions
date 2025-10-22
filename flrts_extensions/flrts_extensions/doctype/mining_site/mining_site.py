# -*- coding: utf-8 -*-
"""Mining Site DocType controller."""

from frappe.model.document import Document


class MiningSite(Document):
    """Mining Site document controller."""

    def validate(self):
        """Validate Mining Site before saving."""
        # Future: Add custom validation logic here
        pass
