# OpenSpec Integration

mcp-guide integrates with OpenSpec, an AI-native system for spec-driven development, providing automatic monitoring and command access for managing changes and specifications.

For more information on OpenSpec, visit https://openspec.dev

## Overview

OpenSpec integration enables structured change management with automatic monitoring of project changes. The integration validates OpenSpec availability, tracks changes, and provides prompt commands for common operations.

## Integration Behaviour

### Initial Validation

When OpenSpec is first enabled, mcp-guide performs one-time validation checks:
- Verifies `openspec` command is installed and available in PATH
- Confirms `openspec/project.md` exists (required by OpenSpec)
- Tests that `openspec list` executes successfully (even if no changes exist)

### Session Monitoring

During each session, the integration:
- Checks OpenSpec version once per session (determines available features)
- Refreshes change list hourly or after agent makes OpenSpec changes
- Caches responses to minimize redundant command execution

### User Experience

The integration may seem verbose in some agents as it executes OpenSpec commands to maintain synchronisation. These commands are necessary for the integration to function correctly. Frequent use of guide tools and prompt commands helps keep OpenSpec and the MCP server synchronised.

## OpenSpec Commands

When OpenSpec is enabled, additional `:openspec/*` commands become available. Some commands invoke the OpenSpec CLI directly (with response caching). Use `@guide :help` for more information (or `/guide :help` in Claude Code or Copilot CLI).

**:openspec/init**
Initialise OpenSpec in the current project using the openspec command. This creates required directory structure and `openspec/project.md` file.

**:openspec/propose** _(openspec/new, openspec/create)_
Initiate a new OpenSpec change by creating the change directory structure and proposal document. Emphasises dialogue with the user before writing documents. Optionally creates tasks.md for tracking implementation.

**:openspec/list**
List all OpenSpec changes in the project. Triggers a refresh of the change list from OpenSpec CLI.

**:openspec/list**
List all OpenSpec changes in the project. Triggers a refresh of the change list from OpenSpec CLI.

**:openspec/show**
Show details for the current or a specific OpenSpec change, including proposal, tasks, and spec deltas.

**:openspec/validate**
Validate the current or a specific OpenSpec change against schema requirements and structural rules.

**:openspec/status**
Get the completion status and percentage for an OpenSpec change based on completed tasks.

**:openspec/archive**
Archive a completed OpenSpec change, moving it to the archive directory and optionally updating main specs.

**:openspec/schemas**
Discover available OpenSpec schemas in the project for creating new specifications.

## Integration with the `workflow` feature flag

When both OpenSpec and workflow feature flags are enabled, they work together:

- The workflow `issue` field typically specifies the OpenSpec change name (e.g., `add-feature-x` or `add-feature-x/sub-spec`)
- mcp-guide provides its own versions of OpenSpec prompts:
  - `:workflow/implement` - Equivalent to openspec-apply (with full project guidelines)
  - `:openspec/archive` - Equivalent to openspec-archive
  - `:openspec/propose` - Equivalent to openspec-propose

Otherwise, OpenSpec and workflow operate independently.

## OpenSpec Template Context

When OpenSpec is enabled, OpenSpec information is available in content templates via `{{openspec.*}}` variables:

- `{{openspec.available}}` - Boolean indicating if OpenSpec is available
- `{{openspec.version}}` - OpenSpec version string
- `{{openspec.changes}}` - Array of change objects with name, status, and task counts
- `{{openspec.show}}` - Details of currently shown change
- `{{openspec.status}}` - Status information for current change

## Configuration

### The `openspec` Feature Flag

This feature flag, normally set at project level, enables OpenSpec integration:

**Boolean:**
- `false` / absent: OpenSpec integration disabled (default)
- `true`: Enable OpenSpec integration with automatic monitoring

When enabled, the OpenSpecTask runs periodically to monitor changes and maintain synchronisation with the OpenSpec CLI.
