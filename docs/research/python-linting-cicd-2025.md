# Python Linting, Formatting, and CI/CD Best Practices for 2025

**Research Date:** October 22, 2025
**Researcher:** Research Agent
**Issue:** [10N-382](https://linear.app/10netzero/issue/10N-382) - Implement Comprehensive Code Quality & CI/CD
**Project:** flrts-extensions (ERPNext custom app, Python 3.11+)

---

## Executive Summary

**Key Finding:** Ruff has emerged as the dominant "all-in-one" tool for Python linting and formatting in 2025, replacing traditional multi-tool stacks (flake8 + pylint + black + isort). However, the traditional stack remains viable and well-supported for projects with specific requirements.

**Recommendations for flrts-extensions:**

1. **Primary Option (Modern):** Ruff for both linting and formatting (10-100x faster, single tool)
2. **Alternative Option (Traditional):** Black (formatting) + Flake8 (linting) + Pylint (deep analysis)
3. **Line Length:** 100 characters (current project standard, aligns with modern practices)
4. **Testing:** pytest 8.2+ with pytest-cov, target 90% coverage initially (60% minimum)
5. **CI/CD:** GitHub Actions with matrix testing across Python 3.11-3.13
6. **Pre-commit:** Essential for local quality gates before commits reach GitHub

---

## 1. Tool Ecosystem Overview (2025)

### 1.1 The Ruff Revolution

**Ruff** (v0.4.x-0.5.x) has fundamentally changed the Python tooling landscape in 2025:

- **Speed:** 10-100x faster than existing tools (written in Rust)
- **Consolidation:** Replaces flake8, pylint, black, isort, pyupgrade, autoflake
- **Compatibility:** 100% Black-compatible formatting, drop-in Flake8 replacement
- **Rules:** 800+ built-in rules covering most common use cases
- **Adoption:** Used by Apache Airflow, FastAPI, Pandas, SciPy, Hugging Face

**Source:** https://docs.astral.sh/ruff/, https://github.com/astral-sh/ruff

**Testimonial (Sebastian Ramirez, FastAPI creator):**
> "Ruff is so fast that sometimes I add an intentional bug in the code just to confirm it's actually running and checking the code."

**Performance Example (Bryan Van de Ven, Bokeh co-creator):**
> "Ruff is ~150-200x faster than flake8 on my machine, scanning the whole repo takes ~0.2s instead of ~20s."

**Source:** Medium - "Ruff vs Old-School Linters" (Oct 2025)

### 1.2 Traditional Tools (Still Maintained)

| Tool | Version | Purpose | Status in 2025 |
|------|---------|---------|----------------|
| **Black** | 24.x | Formatter | Active, still popular, 100% compatible with Ruff formatter |
| **Flake8** | 7.3.0 | PEP 8 linter | Active, legacy projects, largely replaced by Ruff |
| **Pylint** | 4.0.2 | Deep static analysis | Active, used for strict analysis Ruff doesn't cover |
| **isort** | 5.13.x | Import sorter | Active, but Ruff includes import sorting |
| **pytest** | 8.2.x | Testing framework | Active, industry standard |
| **pytest-cov** | 5.0.x | Coverage plugin | Active, essential for coverage |
| **bandit** | 1.7.x | Security scanner | Active, complements Ruff (Ruff doesn't do security) |
| **pre-commit** | 3.7.x | Git hook framework | Active, essential for local CI |

**Sources:**
- Perplexity research (Oct 2025)
- Flake8 release notes: https://flake8.pycqa.org/en/stable/release-notes/index.html
- PyPI package pages

### 1.3 Tool Comparison Matrix

| Feature | Ruff | Black + Flake8 + Pylint |
|---------|------|-------------------------|
| **Speed** | ⚡ Extremely fast (0.2s) | 🐢 Slower (20s+) |
| **Setup** | 🎯 Single tool | 🔧 Multiple configs |
| **Formatting** | ✅ Black-compatible | ✅ Black (authoritative) |
| **Linting** | ✅ 800+ rules | ✅ Comprehensive |
| **Auto-fix** | ✅ Many rules | ⚠️ Limited (Black only) |
| **Plugins** | ❌ No plugin system | ✅ Extensive ecosystem |
| **Deep analysis** | ⚠️ Good, improving | ✅ Pylint excels |
| **Security** | ❌ Use Bandit | ❌ Use Bandit |
| **Type checking** | ❌ Use mypy/pyright | ❌ Use mypy/pyright |

**Recommendation:** Ruff for speed and simplicity; traditional stack if you need specific Pylint rules or plugins that Ruff doesn't support.

**Source:** Comparison from trunk.io, pydevtools.com

---

## 2. Line Length Standards (2025)

### 2.1 Current Industry Consensus

**Line length debate summary:**
- **PEP 8 (1996):** Recommended 79 characters (80 for docstrings)
- **Black default:** 88 characters (introduced 2018)
- **Modern preference:** 100-120 characters (accommodates modern displays)
- **Django:** 119 characters for code, 79 for docstrings

**Key insight:** Black's 88-character default was a compromise between PEP 8 (79) and modern preferences (100-120). In 2025, many teams use 100 as a practical standard.

**flrts-extensions current standard:** 100 characters ✅

**Rationale for 100:**
- Matches modern widescreen displays
- Reduces excessive line breaks
- Common in enterprise codebases (2025)
- Supported by all formatters (Black, Ruff)

**Source:**
- GitHub issue psf/black#290 (community discussion)
- Black documentation: https://black.readthedocs.io/en/stable/guides/using_black_with_other_tools.html
- Dev.to: "VSCode: Setting line lengths in the Black Python code formatter"

### 2.2 Configuration Examples

**For Ruff:**
```toml
[tool.ruff]
line-length = 100
```

**For Black:**
```toml
[tool.black]
line-length = 100
```

**For Flake8 (.flake8 file):**
```ini
[flake8]
max-line-length = 100
```

---

## 3. Configuration Files: Best Practices (2025)

### 3.1 pyproject.toml vs pytest.ini vs .flake8

**Modern standard:** `pyproject.toml` is preferred for centralizing all tool configuration.

**What supports pyproject.toml (2025):**
- ✅ Ruff
- ✅ Black
- ✅ pytest
- ✅ pytest-cov
- ✅ isort
- ✅ Pylint
- ✅ bandit
- ❌ **Flake8 (does NOT support pyproject.toml)** - requires `.flake8` or `setup.cfg`

**Recommendation:** Use `pyproject.toml` for all tools except Flake8. If using Flake8, create a separate `.flake8` configuration file.

**Source:** pytest documentation, Flake8 GitHub issues

### 3.2 Complete pyproject.toml Example (Ruff + pytest)

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "flrts_extensions"
version = "0.1.0"
description = "Custom ERPNext app for FLRTS functionality"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.4.0,<0.6",
    "pytest>=8.2.0,<9",
    "pytest-cov>=5.0.0,<6",
    "bandit>=1.7.0,<2",
    "pre-commit>=3.7.0,<4",
]

# Ruff configuration (linting + formatting)
[tool.ruff]
line-length = 100
target-version = "py311"
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.lint]
# Enable recommended rule sets
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

ignore = [
    "E501",  # Line too long (handled by formatter)
]

# Allow auto-fixing
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.format]
# Use Black-compatible formatting
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

# pytest configuration
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "--cov=flrts_extensions",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=60",
    "-ra",
    "--strict-markers",
    "--strict-config",
]
testpaths = ["tests"]
pythonpath = ["."]
markers = [
    "integration: mark test as integration test (may require ERPNext instance)",
    "slow: mark test as slow-running",
]

# Coverage configuration
[tool.coverage.run]
source = ["flrts_extensions"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Source:**
- Ruff documentation: https://docs.astral.sh/ruff/configuration/
- pytest best practices: https://blog.devgenius.io/pytest-in-2025-a-complete-guide-for-python-developers-9b15ae0fe07e

### 3.3 Alternative: Traditional Stack (Black + Flake8 + Pylint)

**pyproject.toml (Black + Pylint):**
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.pylint.main]
py-version = "3.11"

[tool.pylint.format]
max-line-length = 100

[tool.pylint.messages_control]
disable = [
    "C0111",  # missing-docstring
    "R0903",  # too-few-public-methods
]

[tool.pytest.ini_options]
# Same as above
```

**.flake8 (separate file required):**
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    build,
    dist
per-file-ignores =
    __init__.py:F401
```

**.editorconfig (optional but recommended):**
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{yml,yaml}]
indent_style = space
indent_size = 2
```

---

## 4. pytest Best Practices (2025)

### 4.1 Current Versions and Setup

**pytest:** 8.2.x (latest stable as of October 2025)
**pytest-cov:** 5.0.x (latest stable)

**Coverage thresholds (2025 best practices):**
- **Minimum acceptable:** 60% (initial setup)
- **Production-ready:** 85-90%
- **Critical systems:** 95%+

**Source:** Perplexity research, pytest blog (DevGenius, May 2025)

### 4.2 Directory Structure

```
flrts-extensions/
├── flrts_extensions/          # Source code
│   ├── __init__.py
│   ├── flrts/
│   ├── automations/
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures
│   ├── unit/
│   │   ├── conftest.py        # Unit-specific fixtures
│   │   ├── test_parser_log.py
│   │   └── test_cost_calculation.py
│   └── integration/
│       ├── conftest.py        # Integration-specific fixtures
│       └── test_api_endpoints.py
├── pyproject.toml
└── pytest.ini (optional)
```

**Source:** pytest best practices - https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/

### 4.3 conftest.py Patterns

**Global conftest.py (tests/conftest.py):**
```python
"""Shared fixtures for all tests."""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_frappe():
    """Mock frappe module for unit tests."""
    import sys
    sys.modules['frappe'] = MagicMock()
    yield sys.modules['frappe']
    del sys.modules['frappe']

@pytest.fixture
def sample_parser_log_data():
    """Sample data for FLRTS Parser Log tests."""
    return {
        "telegram_message_id": "12345",
        "openai_request_tokens": 100,
        "openai_response_tokens": 50,
        "openai_model": "gpt-4",
    }
```

**Unit-specific conftest.py (tests/unit/conftest.py):**
```python
"""Fixtures specific to unit tests."""
import pytest

@pytest.fixture(autouse=True)
def reset_state():
    """Reset any global state before each test."""
    yield
    # Cleanup code here
```

**Best practices for fixtures:**
1. Use `autouse=True` sparingly (only for cross-cutting concerns like logging)
2. Prefer function scope for isolation
3. Use fixture factories for parametrizable test data
4. Document fixture purpose with docstrings
5. Group related fixtures logically

**Source:** Python in Plain English - "Mastering pytest" (2025)

### 4.4 Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_parser_log.py

# Run tests matching pattern
pytest -k "test_cost"

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html

# Fail if coverage below threshold
pytest --cov-fail-under=90
```

---

## 5. GitHub Actions CI/CD (2025)

### 5.1 Recommended Workflow Structure

**Three-workflow approach:**
1. **PR Core Checks** (`.github/workflows/pr-core.yml`) - Fast checks on every PR
2. **QA Gate** (`.github/workflows/qa-gate.yml`) - Comprehensive checks before merge
3. **Security Scan** (`.github/workflows/security.yml`) - Weekly security scans

### 5.2 Complete Workflow Examples

**File: `.github/workflows/pr-core.yml`**
```yaml
name: PR Core Checks

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-test:
    name: Lint and Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

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
        run: pytest --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

**File: `.github/workflows/qa-gate.yml`**
```yaml
name: QA Gate

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:

jobs:
  comprehensive-checks:
    name: Comprehensive Quality Checks
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run Ruff (full check)
        run: ruff check --output-format=github .

      - name: Run Ruff format check
        run: ruff format --check --diff .

      - name: Run tests with strict coverage
        run: pytest --cov-fail-under=60 --cov-report=html --cov-report=term

      - name: Archive coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: htmlcov/

      - name: Check for TODO/FIXME comments
        run: |
          if grep -rn "TODO\|FIXME" --include="*.py" flrts_extensions/ tests/; then
            echo "::warning::Found TODO/FIXME comments - consider addressing before merge"
          fi
```

**File: `.github/workflows/security.yml`**
```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  security:
    name: Security Vulnerability Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install bandit[toml]

      - name: Run Bandit security scan
        run: |
          bandit -r flrts_extensions/ -f json -o bandit-report.json || true
          bandit -r flrts_extensions/ -f screen

      - name: Upload Bandit report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bandit-security-report
          path: bandit-report.json
```

**Source:**
- GitHub Actions Python guide: https://docs.github.com/actions/guides/building-and-testing-python
- Atmosly blog: "Python CI/CD Pipeline Mastery" (May 2025)
- Medium: "CI/CD for Python Projects Using GitHub Actions" (Sep 2025)

### 5.3 Matrix Testing Best Practices

**Python version matrix recommendations (2025):**
```yaml
strategy:
  fail-fast: false  # Continue running other versions if one fails
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    # Add 3.13-dev for bleeding edge testing
```

**Why fail-fast: false?**
- See results for all Python versions
- One version's failure doesn't block others
- Useful for identifying version-specific issues

**Source:** Dev.to - "Help test Python 3.13!" (Apr 2025)

---

## 6. Pre-commit Hooks (2025)

### 6.1 Configuration

**File: `.pre-commit-config.yaml`**
```yaml
repos:
  # Ruff linter and formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.7
    hooks:
      # Run the linter
      - id: ruff
        args: [--fix]
      # Run the formatter
      - id: ruff-format

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key
```

**Alternative for traditional stack:**
```yaml
repos:
  # Black formatter
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        args: [--line-length=100]

  # isort import sorter
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  # Flake8 linter
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  # Bandit security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
```

**Source:**
- GitHub: https://github.com/astral-sh/ruff-pre-commit
- Medium: "Effortless Code Quality: Ultimate Pre-Commit Hooks Guide for 2025" (Feb 2025)

### 6.2 Installation and Usage

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate

# Bypass hooks (emergency only)
git commit --no-verify
```

**Installation script: `scripts/install-hooks.sh`**
```bash
#!/bin/bash
set -e

echo "Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

echo "Running pre-commit on all files..."
pre-commit run --all-files || true

echo "✅ Pre-commit hooks installed successfully!"
echo "Hooks will run automatically on git commit."
```

---

## 7. Security Scanning (2025)

### 7.1 Bandit Configuration

**In pyproject.toml:**
```toml
[tool.bandit]
targets = ["flrts_extensions"]
exclude_dirs = ["/tests", "/.venv"]
skips = ["B101"]  # Skip assert_used (common in tests)

[tool.bandit.assert_used]
skips = ["*/tests/*"]
```

**Running Bandit:**
```bash
# Scan with default settings
bandit -r flrts_extensions/

# Scan with config
bandit -c pyproject.toml -r flrts_extensions/

# Generate HTML report
bandit -r flrts_extensions/ -f html -o bandit-report.html

# Scan with specific severity
bandit -r flrts_extensions/ -l high
```

### 7.2 Common Security Issues Detected

**Bandit detects:**
- SQL injection vulnerabilities (B608)
- Shell injection risks (B602)
- Hardcoded passwords/secrets (B105, B106)
- Use of insecure modules (B401-B413)
- Input validation issues
- Information disclosure risks

**Example vulnerable code:**
```python
# B602: subprocess with shell=True
import subprocess
user_input = input("Enter command: ")
subprocess.call(user_input, shell=True)  # UNSAFE!

# B608: SQL injection
username = input("Username: ")
cursor.execute(f"SELECT * FROM users WHERE name='{username}'")  # UNSAFE!

# B105: Hardcoded password
PASSWORD = "admin123"  # UNSAFE!
```

**Source:**
- Krython tutorial: "Security Testing: Bandit and Safety" (Jul 2025)
- Dev.to: "Applying Bandit SAST Tool to Secure Python Applications" (Oct 2025)

---

## 8. Frappe Framework Considerations

### 8.1 Frappe-Specific Linting Notes

**No specific Frappe linting tools identified** in research. The Frappe community discussion from 2021 shows:
- Proposal for code formatters (Black, isort) was discussed
- No Frappe-specific linting rules or plugins found
- Standard Python linting tools work fine for Frappe apps

**Source:** Frappe forum discussion (2021): https://discuss.frappe.io/t/proposal-code-formatters-for-frappe-erpnext-and-bench/72651

### 8.2 Testing Frappe Code

**Key challenges:**
1. Frappe module is not installed in local dev environment
2. DocTypes require ERPNext instance to test
3. Server scripts run in scheduler context (no HTTP request)

**Recommended approach:**
```python
# Mock frappe for unit tests
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_frappe(monkeypatch):
    """Mock frappe module."""
    frappe_mock = MagicMock()
    monkeypatch.setitem(sys.modules, 'frappe', frappe_mock)
    return frappe_mock

def test_cost_calculation(mock_frappe):
    """Test cost calculation logic."""
    # Mock frappe.get_doc
    mock_frappe.get_doc.return_value = MagicMock(
        openai_request_tokens=100,
        openai_response_tokens=50,
    )

    # Test logic
    from flrts_extensions.utils.cost import calculate_cost
    result = calculate_cost("doc-123")
    assert result > 0
```

**Integration tests:**
- Mark with `@pytest.mark.integration`
- May require actual ERPNext instance
- Run separately from unit tests in CI

---

## 9. Current Tool Versions (October 2025)

### 9.1 Recommended Version Constraints

**For requirements-dev.txt:**
```
# Core linting and formatting
ruff>=0.4.0,<0.6

# Alternative: Traditional stack
# black>=24.1.0,<25
# flake8>=7.3.0,<8
# pylint>=4.0.2,<5
# isort>=5.13.0,<6

# Testing
pytest>=8.2.0,<9
pytest-cov>=5.0.0,<6

# Security
bandit[toml]>=1.7.0,<2

# Pre-commit
pre-commit>=3.7.0,<4
```

**For pyproject.toml:**
```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.4.0,<0.6",
    "pytest>=8.2.0,<9",
    "pytest-cov>=5.0.0,<6",
    "bandit[toml]>=1.7.0,<2",
    "pre-commit>=3.7.0,<4",
]
```

**Source:** Perplexity research, PyPI package pages, Flake8 release notes

### 9.2 Version Constraint Rationale

**Why `>=X.Y.Z,<(X+1)` format?**
- Allows minor and patch updates (bug fixes, new features)
- Prevents breaking changes from major version bumps
- Follows semantic versioning best practices
- Ensures CI reproducibility

---

## 10. Implementation Roadmap for flrts-extensions

### 10.1 Recommended Approach (Ruff)

**Phase 1: Configuration**
1. Create `pyproject.toml` with Ruff, pytest, bandit config
2. Create `.pre-commit-config.yaml` with Ruff hooks
3. Create `requirements-dev.txt` or use pyproject.toml optional dependencies

**Phase 2: Fix Existing Issues**
1. Run `ruff check --fix .` to auto-fix 451 issues
2. Manually fix remaining issues (bare except, etc.)
3. Verify with `ruff check .`
4. Format with `ruff format .`

**Phase 3: Testing Setup**
1. Create `tests/` directory structure
2. Write `conftest.py` with Frappe mocks
3. Create initial test suite (cost calculation, utils)
4. Configure pytest in pyproject.toml

**Phase 4: CI/CD**
1. Create `.github/workflows/pr-core.yml`
2. Create `.github/workflows/qa-gate.yml`
3. Create `.github/workflows/security.yml`
4. Test workflows on feature branch

**Phase 5: Pre-commit**
1. Install pre-commit hooks
2. Run on all files
3. Update `CONTRIBUTING.md` with setup instructions

### 10.2 Alternative: Traditional Stack

If Ruff doesn't meet all requirements, use:
- Black for formatting (line-length = 100)
- Flake8 for basic linting (.flake8 config)
- Pylint for deep analysis (pyproject.toml)
- pytest + pytest-cov for testing
- Same CI/CD and pre-commit setup

---

## 11. References and Sources

### 11.1 Official Documentation

1. **Ruff:** https://docs.astral.sh/ruff/
2. **Black:** https://black.readthedocs.io/en/stable/
3. **Flake8:** https://flake8.pycqa.org/en/stable/
4. **pytest:** https://docs.pytest.org/en/stable/
5. **GitHub Actions:** https://docs.github.com/en/actions
6. **pre-commit:** https://pre-commit.com/

### 11.2 Working Examples

1. **Ruff GitHub:** https://github.com/astral-sh/ruff
2. **Ruff pre-commit:** https://github.com/astral-sh/ruff-pre-commit
3. **Real Python Ruff tutorial:** https://realpython.com/ruff-python/

### 11.3 Recent Articles (2025)

1. "Ruff vs Old-School Linters" - Medium PyZilla (Oct 2025)
2. "Python CI/CD Pipeline Mastery" - Atmosly (May 2025)
3. "Pytest in 2025: A Complete Guide" - DevGenius (May 2025)
4. "Effortless Code Quality: Pre-Commit Hooks Guide for 2025" - Medium (Feb 2025)
5. "Comparing Ruff, Flake8, and Pylint" - Trunk.io (Aug 2024)

### 11.4 Community Resources

1. Frappe Forum discussion on formatters (2021)
2. GitHub code search for workflow examples
3. PyPI package pages for version information

---

## 12. Key Takeaways

1. **Ruff is the 2025 standard** - 10-100x faster, replaces multiple tools, Black-compatible
2. **100 character line length** - Modern standard, project already uses this
3. **pyproject.toml** - Central configuration for all tools (except Flake8)
4. **pytest 8.2+** - Current stable, use pyproject.toml config, target 90% coverage
5. **GitHub Actions** - Matrix test Python 3.11-3.13, separate PR and QA workflows
6. **Pre-commit hooks** - Essential for local quality gates
7. **Bandit** - Security scanning complement (Ruff doesn't do security analysis)
8. **Frappe compatibility** - Standard tools work, mock frappe module for unit tests

---

**Research Complete:** October 22, 2025
**Next Step:** Create Research Brief for Linear story enrichment (via Tracking Agent)
