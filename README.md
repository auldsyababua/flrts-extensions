# FLRTS Extensions

[![PR Core Checks](https://github.com/auldsyababua/flrts-extensions/actions/workflows/pr-core.yml/badge.svg)](https://github.com/auldsyababua/flrts-extensions/actions/workflows/pr-core.yml)
[![QA Gate](https://github.com/auldsyababua/flrts-extensions/actions/workflows/qa-gate.yml/badge.svg)](https://github.com/auldsyababua/flrts-extensions/actions/workflows/qa-gate.yml)
[![Security Scan](https://github.com/auldsyababua/flrts-extensions/actions/workflows/security.yml/badge.svg)](https://github.com/auldsyababua/flrts-extensions/actions/workflows/security.yml)

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

For detailed development guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks:**
   ```bash
   ./scripts/install-hooks.sh
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Run linting:**
   ```bash
   ruff check .
   ruff format .
   ```

### Code Quality Standards

- **Linter/Formatter:** Ruff v0.4.x-0.5.x (replaces Black + Flake8 + Pylint)
- **Line Length:** 100 characters
- **Test Coverage:** ≥10% (initial), target ≥60%
- **Testing:** pytest with unit and integration tests
- **Pre-commit Hooks:** Auto-format and lint on commit
- **CI/CD:** GitHub Actions workflows for PR checks, QA gate, and security scans

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov-report=html

# Run only unit tests
pytest tests/unit/

# Skip integration tests (no ERPNext)
pytest -m "not integration"
```

### Linting

```bash
# Check code quality
ruff check .

# Auto-fix issues
ruff check --fix .

# Check formatting
ruff format --check .

# Apply formatting
ruff format .
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
