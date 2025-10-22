## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code quality improvement (refactoring, linting fixes)
- [ ] Infrastructure/tooling update

## Related Issues

<!-- Link to related Linear issues -->

- Refs: 10N-XXX

## Changes Made

<!-- List the main changes in this PR -->

-
-
-

## Testing Performed

<!-- Describe the testing you've done -->

### Unit Tests

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Coverage maintained or improved

### Integration Tests

- [ ] Integration tests pass (if applicable)
- [ ] Manual testing performed on ERPNext instance

### Test Commands Run

```bash
# Add the commands you ran to test your changes
pytest
ruff check .
```

## Checklist

<!-- Verify all items before submitting -->

### Code Quality

- [ ] Code follows project style guidelines (Ruff passes)
- [ ] Code is properly formatted (`ruff format` applied)
- [ ] No linting errors (`ruff check .` passes)
- [ ] Pre-commit hooks installed and passing

### Testing

- [ ] Tests added/updated for changes
- [ ] All tests passing locally
- [ ] Coverage meets minimum threshold (≥10%)
- [ ] Integration tests marked with `@pytest.mark.integration`

### Documentation

- [ ] Code comments added for complex logic
- [ ] README.md updated (if applicable)
- [ ] CONTRIBUTING.md updated (if workflow changes)
- [ ] Docstrings added/updated for new functions

### CI/CD

- [ ] All CI checks passing (PR Core, QA Gate, Security)
- [ ] No new security vulnerabilities introduced
- [ ] Branch is up to date with main

### Deployment (if applicable)

- [ ] Frappe Cloud deployment plan documented
- [ ] Migration scripts added (if schema changes)
- [ ] Environment variables documented (if new configs)
- [ ] Tested on staging bench (if available)

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

## Additional Notes

<!-- Any additional information reviewers should know -->

## Reviewer Guidance

<!-- Help reviewers by highlighting specific areas that need attention -->

- Focus areas for review:
  -
  -

---

**By submitting this PR, I confirm that:**
- I have tested my changes thoroughly
- All CI checks are passing
- I have followed the project's code quality standards
- Documentation has been updated as needed
