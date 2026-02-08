## 1. Parameterize Dockerfile
- [ ] 1.1 Add ARG PYTHON_VERSION=3.14.3 to docker/Dockerfile
- [ ] 1.2 Update FROM statement to use ${PYTHON_VERSION}
- [ ] 1.3 Update docker/compose.yaml to pass PYTHON_VERSION build arg
- [ ] 1.4 Add PYTHON_VERSION to docker/.env.example
- [ ] 1.5 Update docker/README.md with PYTHON_VERSION documentation

## 2. Create Release Workflow
- [ ] 2.1 Create .github/workflows/python-mcp-publish.yml
- [ ] 2.2 Configure workflow_dispatch trigger only
- [ ] 2.3 Add Python setup with PYTHON_VERSION variable
- [ ] 2.4 Add uv installation using astral-sh/setup-uv
- [ ] 2.5 Configure dependency installation with uv

## 3. Add Quality Checks
- [ ] 3.1 Add pytest step for all tests
- [ ] 3.2 Add ruff check for linting
- [ ] 3.3 Add ruff format --check for formatting
- [ ] 3.4 Add mypy step for type checking
- [ ] 3.5 Fail workflow if any check fails

## 4. Add Version Validation
- [ ] 4.1 Parse version from pyproject.toml
- [ ] 4.2 Get latest GitHub release tag
- [ ] 4.3 Compare versions (major.minor.patch)
- [ ] 4.4 Fail if version not incremented
- [ ] 4.5 Allow if no previous release exists

## 5. Configure Docker Publishing
- [ ] 5.1 Add docker/setup-buildx-action for multi-arch
- [ ] 5.2 Add docker/login-action with DOCKERHUB credentials
- [ ] 5.3 Configure docker/build-push-action for amd64 and arm64
- [ ] 5.4 Pass PYTHON_VERSION as build arg
- [ ] 5.5 Tag images with version and latest
- [ ] 5.6 Push to Docker Hub as public images

## 6. Configure PyPI Publishing
- [ ] 6.1 Build package with uv build
- [ ] 6.2 Add pypa/gh-action-pypi-publish step
- [ ] 6.3 Configure PYPI_TOKEN secret
- [ ] 6.4 Publish to pypi.org

## 7. Create GitHub Release
- [ ] 7.1 Extract version-specific notes from CHANGELOG.md
- [ ] 7.2 Create GitHub release with tag
- [ ] 7.3 Attach release notes from CHANGELOG
- [ ] 7.4 Mark as latest release

## 8. Documentation
- [ ] 8.1 Document required secrets in README or docs
- [ ] 8.2 Document required variables
- [ ] 8.3 Document release process
- [ ] 8.4 Add troubleshooting guide

## 9. Testing
- [ ] 9.1 Test workflow with dry-run if possible
- [ ] 9.2 Verify Docker images build for both architectures
- [ ] 9.3 Verify version comparison logic
- [ ] 9.4 Test complete workflow end-to-end
