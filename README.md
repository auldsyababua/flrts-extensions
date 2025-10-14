# FLRTS Extensions

Custom Field Service Management extensions for BigSir FLRTS on ERPNext.

## Overview

FLRTS Extensions provides hook-based event automation and background job
processing for the BigSir FLRTS (Field Reports, Lists, Reminders, Tasks, and
Sub-Tasks) system deployed on Frappe Cloud Private Bench.

## Features

- **Task Event Handlers**: Automated validation and processing for Task DocType
  lifecycle events
- **Telegram Integration**: Webhook endpoint for Telegram Bot API with signature
  validation
- **Background Jobs**: Retry-enabled async processing with exponential backoff
- **Security**: Two-character reveal secret masking and environment-aware
  logging
- **Error Handling**: Comprehensive retry logic for network errors
  (ECONNREFUSED, ETIMEDOUT, HTTP 5xx)

## Installation

### Prerequisites

- ERPNext v15+ on Frappe Cloud Private Bench
- Python 3.10+
- Active Telegram Bot (for webhook features)

### Deployment via Frappe Cloud

1. **Push to Git repository**:

   ```bash
   git add flrts_extensions/
   git commit -m "feat: Add flrts_extensions custom app"
   git push origin main
   ```

2. **Deploy via Frappe Cloud UI**:
   - Navigate to your bench dashboard
   - Trigger deployment from Git
   - Wait for deployment to complete

3. **Run migrations via SSH**:

   ```bash
   ssh <bench-id>@ssh.frappe.cloud
   bench --site <your-site> migrate
   bench restart
   ```

4. **Verify installation**:

   ```bash
   bench --site <your-site> console
   >>> import frappe
   >>> frappe.get_installed_apps()
   # Should include 'flrts_extensions'
   ```

## Configuration

### Required Environment Variables

Set these in `site_config.json` via bench CLI:

```bash
bench --site <your-site> set-config TELEGRAM_BOT_TOKEN "your-bot-token"
bench --site <your-site> set-config TELEGRAM_WEBHOOK_SECRET "your-webhook-secret"
```

See `.env.example` for full configuration reference.

### Telegram Webhook Setup

Configure Telegram webhook to point to your ERPNext site:

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://ops.10nz.tools/api/method/flrts_extensions.automations.telegram_api.handle_telegram_webhook"}'
```

## Architecture

### Hook Registry

Hooks are defined in `hooks.py` and delegate to module functions:

- **doc_events**: Task validation and update handlers
- **scheduler_events**: (Deferred to Phase 2)

### Module Structure

```
flrts_extensions/
├── automations/         # Event handlers and API endpoints
│   ├── task_events.py       # Task DocType hooks
│   ├── telegram_api.py      # Webhook endpoint
│   └── telegram_events.py   # Background message processing
├── utils/               # Shared utilities
│   ├── security.py          # Secret masking
│   └── logging.py           # Environment-aware logging
└── tests/               # Unit tests
```

## Development

### Running Tests

```bash
cd flrts_extensions/
pytest tests/ -v
```

### Linting

```bash
ruff check flrts_extensions/
```

### Type Checking

```bash
mypy flrts_extensions/ --ignore-missing-imports
```

## Monitoring

### Error Logs

View errors in ERPNext:

- Navigate to **Error Log** DocType
- Filter by title: "Automation Error", "Telegram Config Error", etc.

### Background Job Queue

Check queue depth via SSH:

```bash
bench --site <your-site> console
>>> from rq import Queue
>>> from frappe.utils.background_jobs import get_redis_conn
>>> conn = get_redis_conn()
>>> Queue('short', connection=conn).count
```

### Scheduler Status

```bash
bench --site <your-site> scheduler status
```

## Security

- **Secret Masking**: All secrets logged with two-character reveal policy (first
  2 + last 2 chars for secrets ≥ 6 chars, otherwise `***`)
- **Webhook Validation**: Telegram webhooks require
  `X-Telegram-Bot-Api-Secret-Token` header
- **Environment Guards**: Debug logs suppressed in `test` and `production`
  NODE_ENV

## Troubleshooting

### Webhook Not Receiving Messages

1. Verify webhook URL configured:

   ```bash
   curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
   ```

2. Check `TELEGRAM_WEBHOOK_SECRET` matches bot configuration

3. Review Error Log DocType for authentication failures

### Background Jobs Not Processing

1. Check scheduler enabled:

   ```bash
   bench --site <your-site> scheduler status
   ```

2. Verify queue not stalled:

   ```bash
   bench --site <your-site> console
   >>> from rq import Queue
   >>> from frappe.utils.background_jobs import get_redis_conn
   >>> Queue('short', connection=get_redis_conn()).count
   ```

3. Review worker logs for exceptions

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:

- Create GitHub issue:
  [bigsirflrts/issues](https://github.com/auldsyababua/bigsirflrts/issues)
- Email: <ops@10nz.tools>

## Related Documentation

- [ADR-006: ERPNext Frappe Cloud Migration](../docs/architecture/adr/ADR-006-erpnext-frappe-cloud-migration.md)
- [Frappe Cloud Deployment Guide](../docs/deployment/FRAPPE_CLOUD_DEPLOYMENT.md)
- [ERPNext Migration Naming Standards](../docs/erpnext/ERPNext-Migration-Naming-Standards.md)
