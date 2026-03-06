# Changelog

All notable changes to mcp-guide will be documented in this file.

## [1.1.0] - 2026-03-05

### Added
- Permission management MCP tools (`add_permission_path`, `remove_permission_path`)

### Changed
- Refactored prompt prompt templates to provide a more consistent user experience

### Fixed
- Template consistency: all command examples now use `{{@}}guide` prefix

## [1.0.0] - 2026-03-04

### Features
- Content management system with categories and collections
- Template support using Mustache/Chevron syntax
- Multiple transport modes (STDIO, HTTP, HTTPS)
- Feature flags system for project and global configuration
- Workflow management with phase tracking
- OpenSpec integration for spec-driven development
- Command system with guide prompt
- Profile system for pre-configured setups
- Docker support with multi-stage builds
- `guide-agent-install` script for automated agent configuration
- `mcp-install` script for initial install and updating
- `startup-instruction` flag for automatic project context loading on session start
- `update_documents` tool for updating documentation through AI agents
- `autoupdate` global feature flag for automating document update at startup
- Structured logging for installation operations with configurable verbosity

### Changed
- Documentation and deployment to GitHub Pages
- Full Python 3.11+ support and testing
- Console scripts fixed for uvx compatibility
- RetryTask auto-unsubscribes when idle to reduce background overhead
- OpenSpecTask uses on-demand cache refresh instead of proactive updates
- Installation operations use structured logging with DEBUG/INFO/WARNING levels

### Fixed
- Permission command names in templates
- Filesystem tool parameter validation with structured error reporting
- Exit codes for informational flows in installation scripts
- Path validation in `guide-agent-install` to prevent directory traversal
- Missing packaging>=24.0 dependency for version handling
- NameError in workflow tasks when using RenderedContent type annotation
- Workflow monitoring reminder timer event key mismatch
- Path resolution in `guide-agent-install` script preventing agent discovery
- Content-format flag not applied immediately after being set
- Phase-specific template content showing when phase not in workflow configuration
- Scripts not working correctly with uvx due to missing package data
- Docroot safety check prevents updates when docroot equals template source path

## [0.9.0] - 2026-02-16

Initial internal pilot release of mcp-guide.
