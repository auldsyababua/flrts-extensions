"""
Telegram Bot API webhook endpoint for BigSir FLRTS.

Handles incoming webhook requests from Telegram, validates signature,
and enqueues background jobs for message processing.
"""

try:
    import frappe
    from rq import Retry
except ImportError:
    frappe = None
    Retry = None

from flrts_extensions.utils.logging import log_debug, log_error, log_info
from flrts_extensions.utils.security import mask_secret


@frappe.whitelist(allow_guest=True)
def handle_telegram_webhook():
    """
    Public endpoint for Telegram webhooks.

    URL: https://ops.10nz.tools/api/method/flrts_extensions.automations.telegram_api.handle_telegram_webhook

    Flow:
    1. Validate X-Telegram-Bot-Api-Secret-Token header
    2. Parse Telegram update payload
    3. Enqueue background job for processing
    4. Return immediate acknowledgment (< 200ms)

    Returns:
        dict: {"ok": bool, "acknowledged": bool, "processingTime": int}

    Raises:
        frappe.AuthenticationError: If secret token invalid

    Example:
        Telegram sends POST request:
        >>> curl -X POST <endpoint> \
                -H "X-Telegram-Bot-Api-Secret-Token: <secret>" \
                -d '{"update_id": 123, "message": {...}}'
    """
    if not frappe:
        return {"ok": False, "error": "frappe_not_available"}

    try:
        # 1. Validate signature
        incoming_token = frappe.request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        expected_token = frappe.conf.get("TELEGRAM_WEBHOOK_SECRET")

        if not expected_token:
            log_error(
                "TELEGRAM_WEBHOOK_SECRET not configured in site_config.json",
                title="Telegram Config Error",
            )
            frappe.throw("Telegram webhook not configured", frappe.PermissionError)

        if incoming_token != expected_token:
            log_info(
                f"Unauthorized webhook attempt with token: {mask_secret(incoming_token or 'none')}"
            )
            frappe.throw("Unauthorized", frappe.AuthenticationError)

        # 2. Parse payload
        update = frappe.parse_json(frappe.request.data)
        update_id = update.get("update_id")

        log_debug(f"Received Telegram update ID: {update_id}")

        # Extract message or edited_message
        message = update.get("message") or update.get("edited_message")
        if not message:
            log_debug(f"No message in update {update_id}, skipping")
            return {"ok": True, "acknowledged": False, "reason": "no_message"}

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text")

        if not (chat_id and text):
            log_debug(f"Missing chat_id or text in update {update_id}, skipping")
            return {"ok": True, "acknowledged": False, "reason": "incomplete_data"}

        # 3. Enqueue background job (non-blocking)
        retry_config = Retry(max=3, interval=[10, 30, 90])

        frappe.enqueue(
            "flrts_extensions.automations.telegram_events.process_telegram_message",
            update=update,
            queue="short",
            retry=retry_config,
            timeout=60,
        )

        log_info(f"Enqueued processing for Telegram update {update_id} from chat {chat_id}")

        # 4. Return immediate acknowledgment
        return {
            "ok": True,
            "acknowledged": True,
            "processingTime": 0,  # Sync time only (background job queued)
        }

    except frappe.AuthenticationError:
        # Re-raise auth errors (return 401)
        raise

    except Exception as e:
        # Log unexpected errors
        log_error(f"Webhook handler error: {str(e)}", title="Telegram Webhook Error")

        # Return error response (but don't crash)
        return {"ok": False, "acknowledged": False, "error": "internal_error"}
