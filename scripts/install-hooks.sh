#!/bin/bash
# Install pre-commit hooks for flrts-extensions development

set -e

echo "Installing pre-commit hooks for flrts-extensions..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Error: pre-commit is not installed."
    echo "Install it with: pip install pre-commit"
    exit 1
fi

# Install the hooks
pre-commit install

echo "✓ Pre-commit hooks installed successfully!"
echo ""
echo "Hooks will now run automatically on 'git commit'."
echo "To run hooks manually: pre-commit run --all-files"
echo "To bypass hooks (emergency only): git commit --no-verify"
