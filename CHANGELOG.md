# Changelog

All notable changes to mcp-guide will be documented in this file.

## [1.3.0] - 2026-04-25

### Changed
- `autoupdate` is now enabled by default; set it explicitly to `false` to suppress document update prompting
- OpenSpec workflow guidance has been refreshed to align with current OpenSpec CLI usage:
  - Recommend validating changes with `openspec validate <id> --strict --no-interactive` before sharing proposals
  - Archiving guidance now calls out `openspec archive <change-id> --skip-specs --yes` for tooling-only changes and recommends running `openspec validate --strict --no-interactive` after archiving

### Fixed
- Document updates now remove upstream-renamed and deleted files when the local copy is unchanged, while preserving user-edited files

## [1.2.2] - 2026-04-15

### Changed
- `autoupdate` is now enabled by default; set it explicitly to `false` to suppress document update prompting

### Fixed
- Document updates now remove upstream-renamed and deleted files when the local copy is unchanged, while preserving user-edited files

## [1.2.1] - 2026-04-13

### Added
- Better guidance when no project is selected yet
- Qodana static analysis in CI

### Changed
- Guided onboarding is more conversational and state-aware
- Onboarding workflow choices are clearer and align with supported workflow modes
- OpenSpec documentation has been refreshed and clarified

### Fixed
- More consistent no-project behavior across commands and tools
- Improved rendering when a session exists but no project is bound
- Task manager status output renders compactly and consistently in Markdown
- Onboarding workflow wording now matches supported configuration values

## [1.2.0] - 2026-04-10

### Added
- Guided onboarding — configure project preferences across language, workflow, methodology, testing, git,
  and style in a single guided flow; projects without onboarding configured are prompted automatically on session start
- Policy selection — a new `policies` category for optional steering documents organised by topic (e.g. methodology, git operations, commit format)
  - 70+ built-in policy documents covering common preferences across languages and workflows
  - Selected policies are automatically injected into relevant templates at render time
  - When no policy is selected for a topic, the agent proceeds without enforcing a preference
  - Document import provides the ability support custom policies
- Sub-path topic filtering — category patterns can be narrowed by topic prefix without overriding the user's configured selections
- Exploration workflow phase — a new non-ordered `exploration` phase for research-oriented work before committing to a plan, with a dedicated `:explore` command
- Document ingest and export workflows can take advantage of background processing, when available
- Custom document ingest from local files, direct content, and URLs
- Stored document support across content discovery and document management commands
- Full `guide://` URI support through both MCP resources and the `read_resource` tool
- Codex support via `guide://` command URIs for prompt-style command access
- `roots/list_changed` handling for better multi-project IDE support
- Policy selection documentation added to user guide

### Breaking
- Minimum Python version raised from 3.11 to 3.12
  - detail: `PurePosixPath.full_match()` required for stored document pattern matching
- Methodology profiles (`tdd`, `bdd`, `yagni`, `solid`) removed — superseded by policy selection
  - Use the `policies` category to select methodology preferences instead

### Changed
- Core templates no longer embed opinionated choices — these are now injected from the selected policies on a per-project basis
- `guide/methodology` replaces the individual methodology guide documents; content is driven by the project's selected methodology policies
- Migrated from vendored `mcp.server.fastmcp` to standalone `fastmcp` 3.x package providing access to a large number of new features
- Stored document matching behaves consistently with filesystem content discovery
- `category_list_files` can report filesystem files, stored documents, or both
- Server startup no longer requires project context to be immediately available, improving reliability across clients and IDEs
- Consistent error responses across all tools when no project has yet been resolved
- Verbose project info now lists category patterns on separate lines for readability
- Refined to better support multiple concurrent sessions in HTTP mode

### Fixed
- Stale stored document writes are now rejected atomically during mtime-based upserts
- Stored document frontmatter is preserved during content processing
- Session/bootstrap isolation and startup reliability issues across clients
- Direct MCP resource handling for `guide://_command` URIs
- macOS test instability caused by `watchdog` teardown with Python 3.14
- Sessions are now fully isolated, so shared MCP via HTTP works reliably
- Server no longer fails on startup when MCP roots are not yet available


## [1.1.0] - 2026-03-16

### Added
- Permission management MCP tools (`add_permission_path`, `remove_permission_path`) with file-level write permissions
- Export management tools (`list_exports`, `remove_export`) with staleness detection
- Export commands reorganised under `:export/` (`:export/add`, `:export/list`, `:export/remove`)
- `_error` template lambda for structured validation errors in command templates
- Guide prompt parser now supports space-separated flag values (`--flag value` in addition to `--flag=value`)
- Export tracking: exported content is tracked to enable efficient content referencing
- Knowledge indexing support: agents with indexing capabilities (Kiro, Q Developer) receive instructions to index exported content

### Changed
- Reduced MCP tool count from 39 to 28 by consolidating management and introspection tools
- Simplified and reduced the size of MCP tool descriptions
- Removed the default "guide_" prefix on tools
- Command templates now declare required arguments via `argrequired` frontmatter field
- Refactored frontmatter processing and template rendering internals
- Removed introspection mcp tools, consolidated management tools
- Drastically simplified and reduced the size of mcp tool descriptions
- Remove the default "guide_" prefix on tools
- Fixed an issue with the internal task manager statistics (and :project display)
- Refactored internals to provide clear and more consistent template rendering

### Fixed
- Template consistency: all command examples now use `{{@}}guide` prefix
- Task manager statistics display in `:project` status command
- `time_ago` template lambda edge cases in export list output
- Frontmatter rendering in command template partials


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
