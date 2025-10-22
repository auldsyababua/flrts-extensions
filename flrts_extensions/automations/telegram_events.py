"""
Telegram event processing background jobs for BigSir FLRTS.

Handles message processing, sending responses, and external API calls
with full retry handling for network errors.
"""

try:
    import frappe
    import requests
    from rq import Retry
except ImportError:
    frappe = None
    requests = None
    Retry = None

from flrts_extensions.utils.logging import log_debug, log_error, log_info
from flrts_extensions.utils.security import mask_secret

# Network errors that should trigger retry
RETRYABLE_ERRORS = (
    (
        requests.exceptions.ConnectionError,  # ECONNREFUSED, ECONNRESET
        requests.exceptions.Timeout,  # ETIMEDOUT
    )
    if requests
    else ()
)


def process_telegram_message(update):
    """
    Background job for processing Telegram messages.

    Parses message content and takes appropriate action (send reply, create task, etc.).

    Args:
        update: Telegram update dict from webhook

    Example:
        Enqueued via:
        >>> frappe.enqueue("flrts_extensions.automations.telegram_events.process_telegram_message", update={...})
    """
    if not frappe:
        return

    try:
        message = update.get("message") or update.get("edited_message")
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text")

        log_info(f"Processing Telegram message from chat {chat_id}: {text[:50]}...")

        # STUB: Replace with actual message parsing logic
        # For now, just send acknowledgment
        send_telegram_message_async(chat_id, "Message received (stub)")

    except Exception as e:
        log_error(f"Error processing Telegram message: {str(e)}", title="Telegram Processing Error")


def send_telegram_message_async(chat_id, text, retry_count=0):
    """
    Background job for sending Telegram messages with retry logic.

    Handles network errors with exponential backoff per external-api-evidence.md.

    Args:
        chat_id: Telegram chat ID to send message to
        text: Message text
        retry_count: Current retry attempt (for logging)

    Returns:
        dict: {"success": bool, "message_id": int|None, "error": str|None}

    Raises:
        RETRYABLE_ERRORS: Re-raised for RQ retry mechanism
        requests.exceptions.HTTPError: Re-raised for 5xx (RQ retry), logged for 4xx (no retry)

    Example:
        >>> send_telegram_message_async(123456, "Hello!")
        {"success": True, "message_id": 456}
    """
    if not (frappe and requests):
        return {"success": False, "error": "dependencies_not_available"}

    try:
        # Get bot token from config
        bot_token = frappe.conf.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            log_error(
                "TELEGRAM_BOT_TOKEN not configured in site_config.json",
                title="Telegram Config Error",
            )
            return {"success": False, "error": "bot_token_not_configured"}

        log_debug(f"Sending message to chat {chat_id} with bot token: {mask_secret(bot_token)}")

        # Send message via Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

        response = requests.post(url, json=payload, timeout=10)

        # Check for HTTP errors
        response.raise_for_status()

        # Parse response
        result = response.json()

        if not result.get("ok"):
            log_error(f"Telegram API returned ok=false: {result}", title="Telegram API Error")
            return {"success": False, "error": "api_returned_error"}

        message_id = result.get("result", {}).get("message_id")
        log_info(f"Sent Telegram message {message_id} to chat {chat_id}")

        return {"success": True, "message_id": message_id}

    except RETRYABLE_ERRORS as e:
        # Network errors - retry with exponential backoff
        log_info(f"Retryable error on attempt {retry_count + 1}: {str(e)[:100]}")
        raise  # RQ will handle retry

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code

        # 429 Rate Limit - retry with backoff
        if status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", 60))
            log_info(f"Rate limited, retry after {retry_after}s")
            raise  # RQ will retry

        # 5xx Server Error - retry
        if status_code >= 500:
            log_info(f"Server error {status_code}, will retry")
            raise  # RQ will retry

        # 4xx Client Error - don't retry
        if 400 <= status_code < 500:
            log_error(
                f"Client error {status_code} sending message to chat {chat_id}: {str(e)}",
                title="Telegram Send Failed (4xx)",
            )
            return {"success": False, "error": "client_error", "status_code": status_code}

    except Exception as e:
        # Unknown error - log and don't retry
        log_error(
            f"Unknown error sending Telegram message: {str(e)}",
            title="Telegram Send Failed (Unknown)",
        )
        return {"success": False, "error": "unknown"}
