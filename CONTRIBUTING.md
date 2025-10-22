# Contributing to flrts-extensions

Thank you for your interest in contributing to flrts-extensions! This document provides guidelines for development, code quality standards, and contribution workflows.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Development Workflow](#development-workflow)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD Pipeline](#cicd-pipeline)

## Development Setup

### Prerequisites

- Python 3.11+ (matches Frappe Cloud ERPNext v15)
- Git
- pip (Python package manager)

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/auldsyababua/flrts-extensions.git
   cd flrts-extensions
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Install pre-commit hooks:**
   ```bash
   ./scripts/install-hooks.sh
   # OR manually:
   pre-commit install
   ```

4. **Verify installation:**
   ```bash
   ruff check .
   pytest
   ```

## Code Quality Standards

We use **Ruff** (v0.4.x-0.5.x) as our all-in-one linter and formatter, replacing Black, Flake8, and Pylint.

### Code Style

- **Line Length:** 100 characters
- **Indentation:** 4 spaces (NO TABS)
- **Line Endings:** LF (not CRLF)
- **EOF:** All files must end with newline
- **Quotes:** Double quotes for strings
- **Exception Handling:** Use `except Exception:` not bare `except:`

### Running Code Quality Checks

```bash
# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Check formatting
ruff format --check .

# Apply formatting
ruff format .
```

### Code Quality Targets

- **Ruff:** Zero errors
- **Test Coverage:** ≥10% (initial), ≥60% (target)
- **Security:** No Bandit high-severity issues

## Testing Requirements

We use **pytest** for testing with separate unit and integration test suites.

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/               # Unit tests (no external dependencies)
│   └── test_*.py
└── integration/        # Integration tests (require ERPNext)
    └── test_*.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run with coverage report
pytest --cov-report=html

# Skip integration tests (no ERPNext instance)
pytest -m "not integration"
```

### Writing Tests

**Unit tests** should:
- Use the `mock_frappe` fixture to mock Frappe module
- Test business logic in isolation
- Run fast (<100ms per test)
- Not require ERPNext instance

**Integration tests** should:
- Be marked with `@pytest.mark.integration`
- Test interactions between components
- May require ERPNext instance

**Example:**

```python
def test_cost_calculation(mock_frappe):
    """Test cost calculation logic."""
    prompt_tokens = 1000
    completion_tokens = 500
    cost = (prompt_tokens / 1000 * 0.01) + (completion_tokens / 1000 * 0.03)
    assert cost == 0.025
```

## Development Workflow

### 1. Branch Naming

- **Feature:** `feat/10n-xxx-description`
- **Fix:** `fix/10n-xxx-description`
- **Chore:** `chore/description`

### 2. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(doctypes): add FLRTS Parser Log DocType

Refs: 10N-XXX
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `chore`: Maintenance
- `docs`: Documentation
- `test`: Testing
- `refactor`: Code refactoring

### 3. Development Process

1. Create feature branch
2. Make changes
3. Run quality checks locally
4. Commit (pre-commit hooks will run)
5. Push to GitHub
6. Create Pull Request
7. Wait for CI checks to pass
8. Request review
9. Merge after approval

### 4. Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` and will:

**Auto-fix:**
- Trailing whitespace
- EOF newlines
- Ruff formatting
- Import sorting

**Block on errors:**
- Ruff linting failures
- Bandit security issues
- Large files (>1MB)
- Private keys

**Bypass (emergency only):**
```bash
git commit --no-verify
```

## CI/CD Pipeline

Our GitHub Actions workflows ensure code quality:

### PR Core Checks (`pr-core.yml`)

Runs on every PR and push to main:
- ✓ Ruff linting
- ✓ Ruff formatting check
- ✓ pytest with coverage
- ✓ Matrix test (Python 3.11, 3.12, 3.13)

### QA Gate (`qa-gate.yml`)

Comprehensive checks (post-merge + nightly):
- ✓ Full linting suite
- ✓ All tests with coverage reports
- ✓ Upload test artifacts

### Security Scan (`security.yml`)

Weekly security scans:
- ✓ Bandit security scanner
- ✓ Upload security reports

### CI Status Badges

Check README.md for current CI status.

## Frappe-Specific Guidelines

### Module Structure

```
flrts_extensions/
├── flrts/                    # Main module
│   ├── doctype/             # Custom DocTypes
│   ├── report/              # Custom Reports
│   └── server_script/       # Server Scripts
├── automations/             # Event handlers and webhooks
├── fixtures/                # Fixture data
└── hooks.py                 # App hooks
```

### Naming Conventions

- **DocTypes:** PascalCase with spaces (e.g., "FLRTS Parser Log")
- **Fields:** snake_case (e.g., `telegram_message_id`)
- **Custom Fields:** Prefix with `custom_` (e.g., `custom_flrts_source`)
- **Modules:** Uppercase (e.g., "FLRTS")

### Deployment Workflow

1. Make changes locally
2. Commit and push to GitHub
3. Trigger Frappe Cloud deploy via UI
4. SSH to bench and run `bench migrate`
5. Test changes on ops.10nz.tools

## Getting Help

- **Frappe/ERPNext questions:** [Frappe docs](https://frappeframework.com/docs)
- **Project context:** See `.project-context.md`
- **Linear issues:** [BigSirFLRTS project](https://linear.app/10netzero)

## Code Review

All PRs require:
- ✓ All CI checks passing
- ✓ Code review approval
- ✓ No merge conflicts
- ✓ Tests added/updated for changes

---

**Questions?** Open an issue or reach out to the team!
