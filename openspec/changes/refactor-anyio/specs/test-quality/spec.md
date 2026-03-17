## MODIFIED Requirements
### Requirement: Async Test Framework
All async tests SHALL use `@pytest.mark.anyio` as the test marker.
The project MUST NOT depend on `pytest-asyncio`.

#### Scenario: Async test execution
- **WHEN** an async test function is defined
- **THEN** it is decorated with `@pytest.mark.anyio`
- **AND** `pytest-asyncio` is not required

#### Scenario: Test configuration
- **WHEN** pytest is configured in `pyproject.toml`
- **THEN** `asyncio_mode` setting is absent
- **AND** `pytest-asyncio` is not listed in dev dependencies
