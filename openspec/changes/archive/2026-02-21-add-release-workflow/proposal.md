# Change: Add automated release workflow

## Why

Manual releases are error-prone and time-consuming. Need automated workflow that:
- Validates code quality (tests, linting, type checking)
- Ensures version is incremented before release
- Builds and publishes Docker images for multiple architectures
- Publishes Python package to PyPI
- Creates GitHub release with changelog

## What Changes

- Add GitHub Actions workflow for releases (workflow_dispatch with dry-run and prerelease parameters)
- Add dry-run mode that:
  - Runs all validation and builds
  - Shows what commands would execute instead of publishing
  - Explains Docker push, PyPI upload, and GitHub release actions without executing them
- Add prerelease input for explicit pre-release control
- Parallelize publishing steps after validation:
  - Docker multi-arch image builds and push
  - PyPI package build and publish
  - GitHub release creation with artifacts
- Parameterize Dockerfile with PYTHON_VERSION build arg
- Add version comparison logic to prevent duplicate releases
- Integrate best-in-class actions:
  - astral-sh/setup-uv for uv installation
  - actions/setup-python for Python
  - docker/setup-buildx-action for multi-arch builds
  - docker/login-action for Docker Hub auth
  - docker/build-push-action for image publishing
  - pypa/gh-action-pypi-publish for PyPI
- Use CHANGELOG.md for release notes
- Support local Docker builds via .env file

## Impact

- Affected specs: ci-cd (new capability)
- Affected code: docker/Dockerfile (add PYTHON_VERSION arg)
- Required secrets/variables:
  - DOCKERHUB_USERNAME (secret)
  - DOCKERHUB_TOKEN (secret)
  - PYPI_TOKEN (secret)
  - PYTHON_VERSION (variable, e.g., 3.14.3)
- Dependencies: Requires CHANGELOG.md from restructure-documentation
- Releases become consistent, automated, and reliable
