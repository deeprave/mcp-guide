# Integration Tests

This directory contains integration tests that must be run separately from unit tests.

## Running Integration Tests

```bash
# Run integration tests only
pytest tests_integration/

# Run unit tests only (default)
pytest tests/

# DO NOT run both together - this will cause failures
# pytest tests/ tests_integration/  # ❌ Don't do this
```

## Why Separate?

Due to Python's module caching, once tool modules (e.g., `tool_collection.py`) are imported and decorated, the decorators cannot be re-applied. When unit tests import these modules first, the `@tools.tool()` decorators execute and register the tools with FastMCP. If integration tests then try to create a new server instance, the tools won't re-register because the decorator code has already run.

Running the test suites separately ensures each runs in a clean Python process where tool modules are imported fresh and decorators execute properly.
