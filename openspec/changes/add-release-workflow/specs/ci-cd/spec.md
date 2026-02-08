## ADDED Requirements

### Requirement: Parameterized Python Version
The system SHALL support configurable Python version for Docker builds.

#### Scenario: Dockerfile build arg
- **WHEN** Dockerfile is built
- **THEN** PYTHON_VERSION build arg is accepted
- **AND** defaults to 3.14.3 if not provided
- **AND** base image uses specified Python version

#### Scenario: Local development
- **WHEN** building locally
- **THEN** PYTHON_VERSION can be set in .env file
- **AND** docker-compose passes it as build arg
- **AND** .env is gitignored

#### Scenario: CI/CD builds
- **WHEN** workflow builds Docker images
- **THEN** PYTHON_VERSION variable is used
- **AND** same version used for tests and Docker builds

### Requirement: Automated Release Workflow
The system SHALL provide automated release workflow via GitHub Actions.

#### Scenario: Manual trigger only
- **WHEN** release is needed
- **THEN** workflow is triggered via workflow_dispatch
- **AND** workflow does not run on push or PR
- **AND** workflow requires manual approval

#### Scenario: Quality gates
- **WHEN** workflow runs
- **THEN** all tests must pass
- **AND** ruff linting must pass
- **AND** ruff formatting must pass
- **AND** mypy type checking must pass
- **AND** workflow fails if any check fails

### Requirement: Version Validation
The system SHALL validate version increment before release.

#### Scenario: Version comparison
- **WHEN** workflow runs
- **THEN** version is parsed from pyproject.toml
- **AND** latest GitHub release tag is retrieved
- **AND** versions are compared (major.minor.patch)

#### Scenario: Version increment required
- **WHEN** version comparison completes
- **THEN** workflow fails if version not greater than latest
- **AND** workflow succeeds if no previous release exists
- **AND** workflow succeeds if version properly incremented

#### Scenario: Version format
- **WHEN** comparing versions
- **THEN** semantic versioning is enforced
- **AND** major, minor, and patch components are compared
- **AND** clear error message shown if not incremented

### Requirement: Multi-Architecture Docker Publishing
The system SHALL build and publish Docker images for multiple architectures.

#### Scenario: Multi-arch build
- **WHEN** Docker images are built
- **THEN** images are built for linux/amd64
- **AND** images are built for linux/arm64
- **AND** buildx is used for multi-platform support

#### Scenario: Docker Hub publishing
- **WHEN** images are built successfully
- **THEN** images are pushed to Docker Hub
- **AND** images are tagged with version number
- **AND** images are tagged as latest
- **AND** images are marked as public
- **AND** DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are used

#### Scenario: Build args
- **WHEN** Docker images are built
- **THEN** PYTHON_VERSION is passed as build arg
- **AND** same Python version used throughout workflow

### Requirement: PyPI Publishing
The system SHALL publish Python package to PyPI.

#### Scenario: Package build
- **WHEN** quality checks pass
- **THEN** package is built with uv build
- **AND** wheel and sdist are created

#### Scenario: PyPI upload
- **WHEN** package is built
- **THEN** package is published to pypi.org
- **AND** PYPI_TOKEN is used for authentication
- **AND** upload uses official PyPI publish action

### Requirement: GitHub Release Creation
The system SHALL create GitHub release with changelog.

#### Scenario: Release notes
- **WHEN** release is created
- **THEN** notes are extracted from CHANGELOG.md
- **AND** version-specific section is used
- **AND** notes are feature-based, not commit-based

#### Scenario: Release metadata
- **WHEN** release is created
- **THEN** release is tagged with version number
- **AND** release is marked as latest
- **AND** release includes changelog notes

### Requirement: Best-in-Class Actions
The system SHALL use official and recommended GitHub Actions.

#### Scenario: Action selection
- **WHEN** workflow is configured
- **THEN** astral-sh/setup-uv is used for uv
- **AND** actions/setup-python is used for Python
- **AND** docker/setup-buildx-action is used for multi-arch
- **AND** docker/login-action is used for Docker Hub auth
- **AND** docker/build-push-action is used for image publishing
- **AND** pypa/gh-action-pypi-publish is used for PyPI

### Requirement: Release Documentation
The system SHALL document release process and requirements.

#### Scenario: Secret documentation
- **WHEN** setting up releases
- **THEN** required secrets are documented
- **AND** required variables are documented
- **AND** setup instructions are provided

#### Scenario: Process documentation
- **WHEN** performing release
- **THEN** release process is documented
- **AND** troubleshooting guide is available
- **AND** version increment requirements are clear
