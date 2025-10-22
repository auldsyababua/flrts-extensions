import frappe
from frappe.model.document import Document

class FLRTSParserLog(Document):
    def validate(self):
        # Validate confidence score range
        if self.confidence_score is not None and (self.confidence_score < 0 or self.confidence_score > 1):
            frappe.throw("Confidence score must be between 0.0 and 1.0")
        
        # Validate correction chain
        if self.is_correction and not self.original_log_id:
            frappe.throw("Correction logs must reference an original log")
        
        # Validate error state
        if self.error_occurred and not self.error_message:
            frappe.throw("Error message is required when error_occurred is True")
        
        # Validate token fields are non-negative integers if provided
        if self.prompt_tokens is not None and self.prompt_tokens < 0:
            frappe.throw("Prompt tokens must be a non-negative integer")
        if self.completion_tokens is not None and self.completion_tokens < 0:
            frappe.throw("Completion tokens must be a non-negative integer")
        if self.total_tokens is not None and self.total_tokens < 0:
            frappe.throw("Total tokens must be a non-negative integer")