"""
Hook registry for FLRTS Extensions.

This file contains ONLY registry dictionaries - no business logic.
All functions referenced here must be defined in automations/ modules.
"""

app_name = "flrts_extensions"
app_title = "FLRTS Extensions"
app_publisher = "10NetZero"
app_description = "Custom Field Service Management extensions for BigSir FLRTS"
app_version = "0.1.0"
app_license = "MIT"

# Document event hooks
doc_events = {
    "Task": {
        "validate": "flrts_extensions.automations.task_events.validate_task_dependencies",
        "on_update": "flrts_extensions.automations.task_events.handle_task_update"
    }
}

# Scheduled jobs (DEFERRED TO PHASE 2)
# scheduler_events = {
#     "daily": [
#         "flrts_extensions.automations.scheduled_jobs.cleanup_old_logs"
#     ],
#     "cron": {
#         "*/15 * * * *": [
#             "flrts_extensions.automations.scheduled_jobs.sync_telegram_queue"
#         ]
#     }
# }
