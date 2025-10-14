"""
Task DocType event handlers for BigSir FLRTS.

Handles Task lifecycle hooks: validate, on_update, on_submit.
"""

# PROTOTYPE: Import frappe only when available (allows testing outside Frappe context)
try:
    import frappe
    from rq import Retry
except ImportError:
    # Mock imports for testing
    frappe = None
    Retry = None

from flrts_extensions.utils.logging import log_debug, log_info, log_error


def validate_task_dependencies(doc, method):
    """
    Validate hook for Task DocType (runs before save).

    Ensures required fields are populated before allowing save.

    Args:
        doc: Task document instance
        method: Hook method name ("validate")

    Raises:
        frappe.ValidationError: If validation fails

    Example:
        Triggered automatically when Task is saved via:
        >>> task = frappe.get_doc("Task", "TASK-001")
        >>> task.status = "Completed"
        >>> task.save()  # validate hook runs here
    """
    if not frappe:
        return  # Skip in test context

    try:
        log_debug(f"Validating Task {doc.name}")

        # Validation: Completed tasks must have completed_by set
        if doc.status == "Completed" and not doc.get("completed_by"):
            frappe.throw("Completed tasks must have 'Completed By' field set", frappe.ValidationError)

        log_debug(f"Task {doc.name} validation passed")

    except Exception as e:
        # Log validation errors but allow exception to propagate (blocks save)
        log_error(f"Validation error for Task {doc.name}: {str(e)}", title="Task Validation Failed")
        raise


def handle_task_update(doc, method):
    """
    on_update hook for Task DocType (runs after save).

    Enqueues background job for external sync when task status changes.

    Args:
        doc: Task document instance
        method: Hook method name ("on_update")

    Example:
        Triggered automatically after Task save:
        >>> task.status = "Completed"
        >>> task.save()  # on_update hook runs after save
    """
    if not frappe:
        return  # Skip in test context

    try:
        log_info(f"Task {doc.name} updated to status: {doc.status}")

        # Enqueue background job for completed tasks
        if doc.status == "Completed":
            retry_config = Retry(max=3, interval=[10, 30, 90])

            frappe.enqueue(
                "flrts_extensions.automations.task_events.sync_completed_task",
                doc_name=doc.name,
                queue="short",
                retry=retry_config,
                timeout=60
            )

            log_info(f"Enqueued sync job for completed Task {doc.name}")

    except Exception as e:
        # Log error but DON'T re-raise (allow save to succeed)
        log_error(
            f"Failed to enqueue sync job for Task {doc.name}: {str(e)}",
            title="Task Update Hook Failed"
        )


def sync_completed_task(doc_name):
    """
    Background job for syncing completed task to external system.

    STUB IMPLEMENTATION - Replace with actual external API call.

    Args:
        doc_name: Name of Task document to sync

    Returns:
        dict: {"success": bool, "message": str}

    Example:
        Enqueued via:
        >>> frappe.enqueue("flrts_extensions.automations.task_events.sync_completed_task", doc_name="TASK-001")
    """
    if not frappe:
        return {"success": False, "error": "frappe_not_available"}

    try:
        # Fetch document in background context
        doc = frappe.get_doc("Task", doc_name)

        log_info(f"Syncing completed Task {doc_name} to external system (STUB)")

        # STUB: Replace with actual external API call
        # Example:
        # response = requests.post(
        #     f"{EXTERNAL_API_URL}/tasks",
        #     json={"subject": doc.subject, "status": doc.status},
        #     timeout=30
        # )
        # response.raise_for_status()

        log_info(f"Successfully synced Task {doc_name} (STUB)")

        return {"success": True, "message": "Sync completed (stub)"}

    except Exception as e:
        log_error(
            f"Failed to sync Task {doc_name}: {str(e)}",
            title="Task Sync Failed"
        )
        return {"success": False, "error": str(e)}
