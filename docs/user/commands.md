# Prompt Commands

The guide prompt provides a comprehensive command system for direct access to MCP documents and functionality. Commands let you view project information, manage content, control workflows, and configure permissions. All commands follow a consistent structure with built-in help.

## Command Structure

Commands are invoked through the guide prompt with this syntax:

```
@guide :command [args] [--flags]
```

**Examples:**
```
@guide :help
@guide :status
@guide :project
@guide :flags
@guide :create/category docs
```

## Discovery with @guide :help

The `@guide :help` prompt command is your primary discovery mechanism. Use it to explore available commands and their usage:

```
@guide :help              # Show all available commands grouped by category
@guide :help <command>    # Show detailed help for a specific command
```

**Recommended pattern:**
1. Start with `@guide :help` to see available commands
2. Use `@guide :help <command>` for specific command usage
3. Execute the command
4. Use `@guide :help` again to discover related commands

## Core Information Commands

**@guide :status**
Shows system status and current project information including active project, workflow phase (if enabled), and OpenSpec integration status.

**@guide :project** _(:info/project)_
Displays comprehensive project information including project name, categories, collections, feature flags, and filesystem permissions. Use `--verbose` or `-v` for detailed output including all category patterns.

**@guide :flags** _(:info/flags)_
Shows all feature flags affecting the current project - feature flags (apply to all projects by default), project-specific flags (override feature flags), and resolved values (what the agent actually sees).

**@guide :system** _(:info/system)_
Displays system information for both the MCP server and the agent's client environment. Server information (OS, platform, hostname, Python version, working directory) is always shown. Client information (agent's OS, hostname, user, git remotes) requires the `allow-client-info` feature flag to be enabled.

### The `allow-client-info` Feature Flag

Client information collection is gated behind the `allow-client-info` feature flag due to privacy concerns. This flag is normally set globally (affects all projects) and defaults to false. It collects information about the agent's environment (OS, hostname, user) and requires explicit opt-in to respect user privacy. Ask the agent to set the `allow-client-info` feature flag to true to enable it.

## Project Management Commands

**@guide :create/category**
Creates a new category for organising project content. Categories define directories and file patterns for content discovery.

**Examples:**
```
@guide :create/category docs
@guide :create/category --dir documentation --patterns 'README' 'INSTALL' api-docs
@guide :create/category --description 'Testing Guidelines' testing
```

**Parameters:**

- `name` (required) - Category name
- `--dir` - Directory path (defaults to category name)
- `--patterns` - File patterns to match (e.g., `README`, `CONTRIBUTING`, `test_`)
- `--description` - Human-readable description

**@guide :create/collection**
Creates a new collection that groups multiple categories or other collections together.

**Examples:**
```
@guide :create/collection docs
@guide :create/collection api-docs code examples
@guide :create/collection --description 'Getting started content' beginner docs examples
```

**Parameters:**

- `name` (required) - Collection name
- `categories...` - Category or collection names to include
- `--description` - Human-readable description

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

### Permission Commands

Use these commands to view and manage filesystem permissions:

**@guide :perm**
Shows current filesystem permissions configuration for the project - read permissions (project directory + additional paths) and write permissions (allowed write paths).

**@guide :perm/write-add**
Adds a directory to the allowed write paths. Path must be relative to project root and end with `/`: `@guide :perm/write-add src/generated/`

**@guide :perm/read-add**
Adds an absolute path to additional read permissions. Path must be absolute and not a system directory: `@guide :perm/read-add /Users/username/external-docs`

**@guide :perm/write-del**
Removes a directory from allowed write paths.

**@guide :perm/read-del**
Removes a path from additional read permissions.

### Security Violations

When an agent attempts to read or write outside permitted paths, the operation is blocked, a `SecurityError` is raised, the violation is logged, and the agent receives an error message. This ensures that even if an agent is instructed to access restricted paths, the MCP server enforces security boundaries.

## Workflow Commands

When the `workflow` feature flag is enabled, additional workflow commands become available. See [Workflows](workflows.md) for complete documentation.

## OpenSpec Commands

When OpenSpec integration is enabled, OpenSpec commands provide access to spec-driven development features. See [OpenSpec Integration](openspec.md) for complete documentation.
