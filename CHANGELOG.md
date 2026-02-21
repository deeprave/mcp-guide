# Changelog

All notable changes to mcp-guide will be documented in this file.

## [1.0.0] - TBD

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

### Changed
- Documentation and deployment to GitHub Pages
- Full Python 3.11+ support and testing
- Fixed console scripts for uvx compatibility
- RetryTask now auto-unsubscribes when idle to reduce background overhead
- OpenSpecTask uses on-demand cache refresh instead of proactive updates

### Fixed
- Permission command names in templates
- Filesystem tool parameter validation with structured error reporting
- Exit codes for informational flows in installation scripts
- Path validation in `guide-agent-install` to prevent directory traversal
- Added missing packaging>=24.0 for version handling
- NameError in workflow tasks when using RenderedContent type annotation

## [0.9.0] - 2026-02-16

Initial internal pilot release of mcp-guide.

