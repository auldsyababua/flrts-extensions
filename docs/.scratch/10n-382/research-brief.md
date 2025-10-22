# Research Brief - Python Code Quality & CI/CD (10N-382)

**Issue:** [10N-382](https://linear.app/10netzero/issue/10N-382) - Implement Comprehensive Code Quality & CI/CD
**Research Date:** October 22, 2025
**Researcher:** Research Agent

---

## Recommendation: Ruff for Linting and Formatting

**Chosen Approach:** Use **Ruff** (v0.4.x-0.5.x) as the single tool for both linting and formatting, replacing the traditional Black + Flake8 + Pylint stack.

**Version Numbers (October 2025):**
- Ruff: `>=0.4.0,<0.6`
- pytest: `>=8.2.0,<9`
- pytest-cov: `>=5.0.0,<6`
- bandit: `>=1.7.0,<2`
- pre-commit: `>=3.7.0,<4`

---

## Rationale

**Why Ruff over traditional tools:**
1. **10-100x faster** than Flake8/Black/Pylint (written in Rust)
2. **Single tool** replaces multiple (Flake8, Black, isort, pyupgrade, autoflake)
3. **100% Black-compatible** formatting (zero style differences)
4. **800+ built-in rules** covering most common use cases
5. **Industry adoption** by Apache Airflow, FastAPI, Pandas, SciPy, Hugging Face
6. **Active development** by Astral (same team as uv package manager)

**What alternatives were rejected:**
- **Black + Flake8 + Pylint:** Still viable but slower, requires multiple tools and configs
- **Black alone:** No linting capability
- **Pylint alone:** Slow, no auto-formatting

**Confidence Level:** High (based on 2025 industry trends and performance benchmarks)

---

## Critical Findings

### Line Length Standard
- **Project current:** 100 characters ✅
- **Industry 2025:** 100-120 characters is modern standard
- **Black default:** 88 characters (older standard from 2018)
- **Recommendation:** Keep 100 characters (aligns with modern practices)

### Python Version Support
- **Target:** Python 3.11+ (matches Frappe Cloud ERPNext v15)
- **CI Testing:** Matrix test across 3.11, 3.12, 3.13 for compatibility
- **Latest stable pytest:** 8.2.x (full Python 3.11-3.13 support)

### Coverage Thresholds (2025 Best Practices)
- **Minimum acceptable:** 60% (initial setup for flrts-extensions)
- **Production-ready:** 85-90%
- **Critical systems:** 95%+

### Security Scanning
- **Ruff does NOT include security scanning**
- **Must use Bandit** separately for security vulnerability detection
- **Bandit detects:** SQL injection, shell injection, hardcoded passwords, insecure modules

### Frappe Framework Compatibility
- **No Frappe-specific linting tools** exist
- **Standard Python tools work** fine for Frappe apps
- **Testing challenge:** Must mock `frappe` module for unit tests (not installed locally)
- **Integration tests:** May require actual ERPNext instance, mark with `@pytest.mark.integration`

---

## Code Examples & References

### Official Documentation

**Ruff:**
- Main docs: https://docs.astral.sh/ruff/
- Configuration: https://docs.astral.sh/ruff/configuration/
- GitHub: https://github.com/astral-sh/ruff (43.2k stars)
- Pre-commit: https://github.com/astral-sh/ruff-pre-commit

**pytest:**
- Official docs: https://docs.pytest.org/en/stable/
- Configuration: https://docs.pytest.org/en/stable/reference/customize.html
- Best practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html

**GitHub Actions:**
- Python workflow guide: https://docs.github.com/en/actions/guides/building-and-testing-python
- Workflow syntax: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions

### Working Code Examples

**1. pyproject.toml (Ruff + pytest configuration):**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "flrts_extensions"
version = "0.1.0"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
    "ruff>=0.4.0,<0.6",
    "pytest>=8.2.0,<9",
    "pytest-cov>=5.0.0,<6",
    "bandit[toml]>=1.7.0,<2",
    "pre-commit>=3.7.0,<4",
]

# Ruff configuration
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
]
ignore = ["E501"]  # Line too long (handled by formatter)
fixable = ["ALL"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# pytest configuration
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "--cov=flrts_extensions",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=60",
]
testpaths = ["tests"]

[tool.coverage.run]
source = ["flrts_extensions"]
omit = ["*/tests/*", "*/migrations/*"]
```

**Source:** https://docs.astral.sh/ruff/configuration/

**2. .pre-commit-config.yaml (Ruff + Bandit):**

```yaml
repos:
  # Ruff linter and formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.7
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
```

**Source:** https://github.com/astral-sh/ruff-pre-commit

**3. GitHub Actions Workflow (.github/workflows/pr-core.yml):**

```yaml
name: PR Core Checks

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          allow-prereleases: true
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run Ruff linter
        run: ruff check .

      - name: Run Ruff formatter check
        run: ruff format --check .

      - name: Run tests with coverage
        run: pytest --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
```

**Source:** https://docs.github.com/en/actions/guides/building-and-testing-python

**4. conftest.py (Mock Frappe for unit tests):**

```python
"""Shared pytest fixtures."""
import pytest
import sys
from unittest.mock import MagicMock

@pytest.fixture
def mock_frappe():
    """Mock frappe module for unit tests."""
    frappe_mock = MagicMock()
    sys.modules['frappe'] = frappe_mock
    yield frappe_mock
    del sys.modules['frappe']

@pytest.fixture
def sample_parser_log_data():
    """Sample FLRTS Parser Log data."""
    return {
        "telegram_message_id": "12345",
        "openai_request_tokens": 100,
        "openai_response_tokens": 50,
    }
```

**5. Example Unit Test:**

```python
"""Test cost calculation logic."""

def test_calculate_cost(mock_frappe, sample_parser_log_data):
    """Test OpenAI cost calculation."""
    # Mock frappe.get_doc
    mock_doc = MagicMock(**sample_parser_log_data)
    mock_frappe.get_doc.return_value = mock_doc

    # Import after mocking frappe
    from flrts_extensions.utils.cost import calculate_cost

    result = calculate_cost("doc-123")
    assert result > 0
    mock_frappe.get_doc.assert_called_once_with(
        "FLRTS Parser Log", "doc-123"
    )
```

### Version-Specific Syntax

**Ruff CLI usage (v0.4.x-0.5.x):**
```bash
# Check for issues
ruff check .

# Fix issues automatically
ruff check --fix .

# Format code
ruff format .

# Check formatting without modifying
ruff format --check .

# Show GitHub Actions annotations
ruff check --output-format=github .
```

**pytest CLI usage (v8.2.x):**
```bash
# Run tests with coverage
pytest

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html

# Fail if coverage below threshold
pytest --cov-fail-under=90
```

---

## Implementation Notes

### Key Gotchas

1. **Flake8 does NOT support pyproject.toml** - If using Flake8, must create separate `.flake8` file
2. **Ruff auto-fix can make many changes** - Review diffs carefully before committing
3. **Pre-commit hooks may slow down commits** - But catch issues before CI (faster overall)
4. **Frappe module not installed locally** - Must mock for unit tests
5. **Coverage should fail CI** - Use `--cov-fail-under=60` to prevent coverage regression
6. **Python 3.13 is still in beta** - Use `allow-prereleases: true` in GitHub Actions

### Required Configuration Files

**Must create:**
1. `pyproject.toml` - Ruff, pytest, bandit config
2. `.pre-commit-config.yaml` - Git hooks
3. `.github/workflows/pr-core.yml` - Fast PR checks
4. `.github/workflows/qa-gate.yml` - Comprehensive checks
5. `.github/workflows/security.yml` - Weekly security scan
6. `tests/conftest.py` - Shared test fixtures
7. `requirements-dev.txt` OR use `pyproject.toml` optional dependencies
8. `.editorconfig` - Editor consistency (optional but recommended)

**Do NOT create:**
- `pytest.ini` - Use pyproject.toml instead
- `.flake8` - Not needed if using Ruff

### Common Errors and Solutions

**Error:** `ModuleNotFoundError: No module named 'frappe'`
**Solution:** Mock frappe in conftest.py for unit tests

**Error:** Ruff finds 451 issues
**Solution:** Run `ruff check --fix .` to auto-fix most issues

**Error:** Pre-commit hooks failing
**Solution:** Run `pre-commit run --all-files` to see all issues, fix one by one

**Error:** Coverage below threshold
**Solution:** Write more tests OR temporarily lower threshold for initial setup

---

## References

**Deep Research:** `/Users/colinaulds/Desktop/flrts-extensions/docs/research/python-linting-cicd-2025.md`

**Official Docs:**
- Ruff: https://docs.astral.sh/ruff/
- pytest: https://docs.pytest.org/
- GitHub Actions: https://docs.github.com/en/actions
- Bandit: https://bandit.readthedocs.io/

**Working Examples:**
- FastAPI (uses Ruff): https://github.com/tiangolo/fastapi
- Pandas (uses Ruff): https://github.com/pandas-dev/pandas
- Real Python tutorial: https://realpython.com/ruff-python/

**Recent Guides (2025):**
- "Ruff vs Old-School Linters" (Medium, Oct 2025)
- "Python CI/CD Pipeline Mastery" (Atmosly, May 2025)
- "Pytest in 2025: Complete Guide" (DevGenius, May 2025)

---

**Research Status:** ✅ Complete
**Confidence Level:** High
**Next Agent:** Planning Agent (for handoff to Action Agent)
**Estimated Implementation Time:** 20-24 hours across 6 child issues
