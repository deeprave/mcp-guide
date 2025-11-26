# project-config Specification

## Purpose
TBD - created by archiving change python-dev-environment. Update Purpose after archive.
## Requirements
### Requirement: Python Project Structure
The project SHALL use a monorepo structure with two separate packages for separation of concerns.

#### Scenario: Package organization
- WHEN the project is built
- THEN `mcp_core` package contains reusable core functionality
- AND `mcp_guide` package contains guide-specific implementation
- AND both packages are independently importable

### Requirement: Dependency Management
The project SHALL use uv for dependency management with separate regular and development dependencies.

#### Scenario: Regular dependencies
- WHEN the project is installed
- THEN all regular dependencies are available for runtime use
- AND dependencies include: mcp[cli], pydantic, pyyaml, aiohttp, aioshutil, aiofiles, chevron

#### Scenario: Development dependencies
- WHEN development environment is set up
- THEN all dev dependencies are available for testing and tooling
- AND dependencies include: pytest, pytest-asyncio, pytest-cov, coverage, ruff, mypy, pre-commit, type stubs

### Requirement: Testing Configuration
The project SHALL use pytest with asyncio support and coverage reporting.

#### Scenario: Test execution
- WHEN tests are run via `uv run pytest`
- THEN pytest discovers tests in `tests/` directory
- AND async tests are handled automatically
- AND coverage is measured for `src/` packages
- AND coverage report shows missing lines

### Requirement: Code Quality Tools
The project SHALL use ruff for linting/formatting and mypy for type checking.

#### Scenario: Linting and formatting
- WHEN code is checked via `uv run ruff check`
- THEN import sorting is enforced
- AND line length is limited to 120 characters
- AND Python 3.13 syntax is targeted

#### Scenario: Type checking
- WHEN code is checked via `uv run mypy`
- THEN strict type checking is enforced
- AND all type errors are reported

### Requirement: Template System
The project SHALL use Chevron for Mustache-based template rendering.

#### Scenario: Template availability
- WHEN templates are needed
- THEN all templates are available in `templates/` directory
- AND templates use `.md.mustache` extension
- AND templates are included in package distribution

### Requirement: Security Scanning
The project SHALL use osvcheck for vulnerability scanning in pre-commit hooks.

#### Scenario: Vulnerability detection
- WHEN code is committed
- THEN osvcheck scans for known vulnerabilities
- AND commit is blocked if vulnerabilities are found

### Requirement: Build System
The project SHALL use uv_build as the build backend with uv build.

#### Scenario: Package building
- WHEN `uv build` is executed
- THEN wheel and sdist are created
- AND both packages are included
- AND templates are included as package data
- AND uv_build backend is used (not hatchling)

### Requirement: Project Metadata
The project SHALL have complete metadata for PyPI distribution.

#### Scenario: Package information
- WHEN package is published
- THEN name is `mcp-guide`
- AND version starts at `0.5.0`
- AND description is present
- AND license is MIT
- AND Python requirement is `>=3.13`
- AND appropriate classifiers are set

