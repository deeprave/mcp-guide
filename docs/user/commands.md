# Prompt Commands

mcp-guide provides a comprehensive command system through the guide prompt, enabling agents to access project information, manage content, and control workflow behaviour.

## Overview

The guide prompt is the primary interface for interacting with mcp-guide. Commands provide access to project configuration, system information, content management, and workflow control. All commands follow a consistent structure and provide built-in help.

## Command Structure

Commands are invoked through the guide prompt with this syntax:

```
:command [args] [--flags]
```

**Examples:**
```
:help
:status
:project
:flags
:create/category docs
```

## Discovery with :help

The `:help` command is your primary discovery mechanism. Use it to explore available commands and their usage:

```
:help              # Show all available commands grouped by category
:help <command>    # Show detailed help for a specific command
```

**Recommended pattern:**
1. Start with `:help` to see available commands
2. Use `:help <command>` for specific command usage
3. Execute the command
4. Use `:help` again to discover related commands

## Core Information Commands

### :status

Shows system status and current project information including active project, workflow phase (if enabled), and OpenSpec integration status (again, if enabled).

**Usage:** `:status`

### :project _(:info/project)_

Displays comprehensive project information including:
- Project name and configuration
- Categories and their directories
- Collections and their category memberships
- Feature flags (project-level)
- Filesystem permissions

**Usage:** `:project` or `:info/project`

Use `--verbose` or `-v` for detailed output including all category patterns.

### :flags _(:info/flags)_

Shows all feature flags affecting the current project:
- Feature flags (apply to all projects by default)
- Project-specific flags (override feature-flags)
- Resolved values (what the agent actually sees)

**Usage:** `:flags` or `:info/flags`

Feature flags control behaviour like workflow support, OpenSpec integration, and client information collection.

### :system _(:info/system)_

Displays system information for both the MCP server and the agent's client environment.

**Server information** (always shown):
- Operating system and platform
- Hostname
- Python version
- Working directory

**Client information** (requires `allow-client-info` feature flag to be enabled):
- Agent's operating system and platform
- Agent's hostname
- User name
- Git remote URLs

**Usage:** `:system` or `:info/system`

#### The `allow-client-info` Feature Flag

Client information collection is gated behind the `allow-client-info` feature flag due to privacy concerns. This flag is normally set globally (affects all projects) and defaults to _false_.

**Why it's gated:**
- Collects information about the agent's environment (OS, hostname, user)
- Requires explicit opt-in to respect user privacy

**To enable:**
Ask the agent to set the `allow-client-info` feature flag to true.

When disabled, `:system` shows only server information and indicates that client info collection is disabled.

## Project Management Commands

### :create/category

Creates a new category for organising project content. Categories define directories and file patterns for content discovery.

**Usage:** `:create/category [--dir <path>] [--patterns <pattern>...] [--description <text>] <name>`

**Examples:**
```
:create/category docs
:create/category --dir documentation --patterns '*.md' '*.rst' api-docs
:create/category --description 'Test files' tests
```

**Parameters:**
- `name` (required): Category name
- `--dir`: Directory path (defaults to category name)
- `--patterns`: File patterns to match (e.g., `*.md`, `*.py`)
- `--description`: Human-readable description

### :create/collection

Creates a new collection that groups multiple categories or other collections together.

**Usage:** `:create/collection [--description <text>] <name> [categories...]`

**Examples:**
```
:create/collection docs
:create/collection api-docs code examples
:create/collection --description 'Getting started content' beginner docs examples
```

**Parameters:**
- `name` (required): Collection name
- `categories...`: Category or collection names to include
- `--description`: Human-readable description

Collections enable logical grouping of related content for easier access through the @guide prompt.

## Filesystem Permissions

mcp-guide implements built-in security controls to ensure agent instructions don't transgress security boundaries outside the project.

### Security Model

**Read permissions:**
- Project directory: Always readable (default)
- Additional paths: Must be explicitly allowed via `additional_read_paths` in project configuration
- System directories: Always blocked (e.g., `/etc`, `/System`, `C:\Windows`)

**Write permissions:**
- Controlled by `allowed_write_paths` in project configuration
- Paths must be relative to project root
- Must end with trailing slash (e.g., `src/`, `docs/`)
- Default: Empty list (no writes allowed outside explicit configuration)

**Temporary files:**
- Safe temp paths are allowed for read/write
- System validates temp directory safety

### :perm

Shows current filesystem permissions configuration for the project.

**Usage:** `:perm`

**Displays:**
- Read permissions (project directory + additional paths)
- Write permissions (allowed write paths)

### :perm/write-add

Adds a directory to the allowed write paths. Path must be relative to project root and end with `/`.

**Usage:** `:perm/write-add <path>`

**Example:** `:perm/write-add src/generated/`

### :perm/read-add

Adds an absolute path to additional read permissions. Path must be absolute and not a system directory.

**Usage:** `:perm/read-add <path>`

**Example:** `:perm/read-add /Users/username/external-docs`

### :perm/write-del

Removes a directory from allowed write paths.

**Usage:** `:perm/write-del <path>`

### :perm/read-del

Removes a path from additional read permissions.

**Usage:** `:perm/read-del <path>`

### Security Violations

When an agent attempts to read or write outside permitted paths:
1. The operation is blocked
2. A `SecurityError` is raised
3. The violation is logged
4. The agent receives an error message

This ensures that even if an agent is instructed to access restricted paths, the MCP server enforces security boundaries.

## Workflow Commands

When the `workflow` feature flag is enabled, additional `:workflow/*` commands become available. See [Workflows](workflows.md) for complete documentation.

**Key workflow commands:**
- `:workflow/show` (`:show`) - Show current workflow status
- `:workflow/phase` (`:phase`) - Transition to a specific phase
- `:workflow/issue` (`:issue`) - Manage current issue
- `:workflow/check` (`:check`) - Run code quality checks
- `:workflow/review` (`:review`) - Delegate review to guide-review agent

## OpenSpec Commands

When OpenSpec integration is enabled, `:openspec/*` commands provide access to spec-driven development features. See [OpenSpec Integration](openspec.md) for complete documentation.

**Key OpenSpec commands:**
- `:openspec/propose` - Create new OpenSpec change
- `:openspec/list` - List all changes
- `:openspec/show` - Show change details
- `:openspec/status` - Get completion status
- `:openspec/validate` - Validate change against schema

## Command Categories

Commands are organised into categories for easier discovery:

**General:** `:status`, `:help`
**Info:** `:project`, `:flags`, `:system`, `:agent`
**Project:** `:create/category`, `:create/collection`
**Permissions:** `:perm`, `:perm/write-add`, `:perm/read-add`, `:perm/write-del`, `:perm/read-del`
**Workflow:** `:workflow/*` commands (when enabled)
**OpenSpec:** `:openspec/*` commands (when enabled)

Use `:help` to see all available commands in your current configuration.

## Best Practices

### For Users

- **Start with :help** - Discover available commands before diving in
- **Use :status regularly** - Stay aware of current project and workflow state
- **Check :flags** - Understand which features are enabled
- **Review :perm** - Know your filesystem boundaries
- **Enable features deliberately** - Use feature flags to control agent behaviour

### For Agents

- **Respect security boundaries** - Don't attempt to bypass filesystem restrictions
- **Use discovery commands** - Call `:help` to learn available functionality
- **Check permissions first** - Use `:perm` before attempting file operations
- **Follow workflow phases** - Respect phase restrictions when workflow is enabled
- **Provide context** - Use `--verbose` flags when users need detailed information

## Next Steps

- **[Workflows](workflows.md)** - Structured development phase tracking
- **[OpenSpec Integration](openspec.md)** - Spec-driven development workflow
- **[Feature Flags](feature-flags.md)** - Configuring project and global behaviour
- **[Content Management](content-management.md)** - Working with categories and collections
- **[Developer Documentation](../developer/command-authoring.md)** - Creating custom commands
