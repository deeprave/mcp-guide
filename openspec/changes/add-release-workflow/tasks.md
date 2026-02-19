## 1. Parameterize Dockerfile
- [x] 1.1 Add ARG PYTHON_VERSION=3.14.3 to docker/Dockerfile
- [x] 1.2 Update FROM statement to use ${PYTHON_VERSION}
- [x] 1.3 Update docker/compose.yaml to pass PYTHON_VERSION build arg
- [x] 1.4 Add PYTHON_VERSION to docker/.env.example
- [x] 1.5 Update docker/README.md with PYTHON_VERSION documentation

## 2. Create Release Workflow
- [x] 2.1 Create .github/workflows/python-mcp-publish.yml
- [x] 2.2 Configure workflow_dispatch trigger with inputs:
  - [x] dry-run (boolean): show commands without publishing
  - [x] prerelease (boolean): mark as pre-release in GitHub
- [x] 2.3 Add Python setup with PYTHON_VERSION variable
- [x] 2.4 Add uv installation using astral-sh/setup-uv
- [x] 2.5 Configure dependency installation with uv

## 3. Add Quality Checks
- [x] 3.1 Add pytest step for all tests
- [x] 3.2 Add ruff check for linting
- [x] 3.3 Add ruff format --check for formatting
- [x] 3.4 Add mypy step for type checking
- [x] 3.5 Fail workflow if any check fails

## 4. Add Version Validation
- [x] 4.1 Parse version from pyproject.toml
- [x] 4.2 Get latest GitHub release tag
- [x] 4.3 Compare versions (major.minor.patch)
- [x] 4.4 Fail if version not incremented
- [x] 4.5 Allow if no previous release exists

## 5. Configure Docker Publishing
- [x] 5.1 Add docker/setup-buildx-action for multi-arch
- [x] 5.2 Add docker/login-action with DOCKERHUB credentials (skip in dry-run)
- [x] 5.3 Configure docker/build-push-action for amd64 and arm64
- [x] 5.4 Pass PYTHON_VERSION as build arg
- [x] 5.5 Tag images with version and latest
- [x] 5.6 In dry-run: show Docker commands without pushing
- [x] 5.7 In production: push to Docker Hub as public images
- [x] 5.8 Parallelize with PyPI and GitHub release steps after validation

## 6. Configure PyPI Publishing
- [x] 6.1 Build package with uv build
- [x] 6.2 Add pypa/gh-action-pypi-publish step
- [x] 6.3 Configure PYPI_TOKEN secret
- [x] 6.4 In dry-run: show PyPI upload commands without publishing
- [x] 6.5 In production: publish to pypi.org
- [x] 6.6 Run in parallel with Docker and GitHub release steps

## 7. Create GitHub Release
- [x] 7.1 Extract version-specific notes from CHANGELOG.md
- [x] 7.2 In dry-run: show release details without creating
- [x] 7.3 In production: create GitHub release with tag
- [x] 7.4 Set prerelease flag based on workflow input
- [x] 7.5 Attach release notes from CHANGELOG
- [x] 7.6 Mark as latest release (only if not prerelease)
- [x] 7.7 Run in parallel with Docker and PyPI steps

## 8. Documentation
- [x] 8.1 Document required secrets in README or docs
- [x] 8.2 Document required variables
- [x] 8.3 Document release process with dry-run option
- [x] 8.4 Add troubleshooting guide

## 9. Testing
- [x] 9.1 Test workflow with dry-run mode enabled
- [x] 9.2 Verify dry-run shows commands without executing
- [x] 9.3 Verify Docker images build for both architectures
- [x] 9.4 Verify version comparison logic
- [x] 9.5 Test complete workflow end-to-end in production mode
