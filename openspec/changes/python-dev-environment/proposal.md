# Proposal: Python Development Environment Setup

## Metadata
- **Epic**: MG-18 - MCP Guide Architectural Reboot
- **Issue**: MG-19 - Establish project dev environment
- **Assignee**: David Nugent

## Overview
Set up the Python development environment for mcp-guide v2 with proper project structure, dependencies, and tooling configuration.

## Motivation
Establish a clean, well-configured Python project foundation that:
- Separates core reusable functionality (`mcp_core`) from guide-specific implementation (`mcp_guide`)
- Provides comprehensive development tooling (testing, linting, type checking)
- Enables template-based content generation with Chevron
- Maintains security through vulnerability scanning
- Follows modern Python packaging standards with uv

## Context
This is the foundational setup for mcp-guide v2, a clean reimplementation of mcp-server-guide with correct architectural patterns. The project will use:
- Python 3.13+ with modern typing
- FastMCP for MCP server implementation
- Monorepo structure with two packages for separation of concerns
- Template-based content generation for flexibility

## Objectives
1. Configure project metadata and structure
2. Install all required dependencies
3. Set up development tooling (pytest, ruff, mypy, pre-commit)
4. Copy and adapt templates from mcp-server-guide
5. Configure build system and package distribution

## Requirements

### Project Structure
- Monorepo with two packages:
  - `src/mcp_core/` - Reusable core functionality
  - `src/mcp_guide/` - Guide-specific implementation
- `templates/` directory with Mustache templates
- `src/osvcheck.py` for vulnerability scanning
- Standard Python project files (README.md, LICENSE.md, .gitignore, etc.)

### Dependencies

#### Regular Dependencies
- mcp[cli] - MCP server framework
- pydantic - Data validation
- pyyaml - YAML configuration
- aiohttp - Async HTTP client
- aioshutil - Async file operations
- aiofiles - Async file I/O
- chevron - Mustache templating
- click - CLI framework with reliable testing support

#### Development Dependencies
- pytest - Testing framework
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting
- coverage - Coverage measurement
- ruff - Linting and formatting
- mypy - Type checking
- pre-commit - Git hooks
- types-aiofiles - Type stubs
- types-pyyaml - Type stubs
- mcp-inspector - MCP protocol testing and integration tests

### Configuration

#### pyproject.toml
- Project name: `mcp-guide`
- Version: `0.5.0`
- Python requirement: `>=3.13`
- Build system: uv_build (uv's native build backend)
- Tool configurations from mcp-server-guide:
  - pytest with asyncio support
  - ruff with import sorting
  - mypy with strict mode

#### Templates
- Copy all templates from `../mcp-server-guide/templates/`
- Rename `.md` files to `.md.mustache`
- Maintain directory structure

#### Security
- Copy `osvcheck.py` from mcp-server-guide
- Configure pre-commit hook for vulnerability scanning

#### Testing Infrastructure
- Copy test isolation, hooks, and fixtures from mcp-server-guide's `conftest.py` on-demand as requirements arise
- Ensure tests are isolated from production directories

## Assumptions
- uv is already installed and available
- mcp-server-guide project exists at `../mcp-server-guide`
- Python 3.13+ is available
- Git repository is already initialized

## Out of Scope
- Implementation of actual MCP server functionality
- Migration of existing code from v1
- Documentation beyond basic README
- CI/CD configuration

## Success Criteria
- [ ] All dependencies installed successfully
- [ ] Project structure matches specification
- [ ] All dev tools configured and working (pytest, ruff, mypy)
- [ ] Templates copied and renamed correctly
- [ ] `uv build` completes successfully
- [ ] Pre-commit hooks installed and passing
- [ ] Project metadata complete and accurate
