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

**@guide :project** _(:info/project, :project/info)_
Displays comprehensive project information including project name, categories, collections, feature flags, and filesystem permissions. Use `--verbose` or `-v` for detailed output including all category patterns.

**@guide :flags**
Shows all feature flags affecting the current project - feature flags (apply to all projects by default), project-specific flags (override feature flags), and resolved values (what the agent actually sees). Lists available flags with their scope restrictions (Project only, Feature only, or both).

**@guide :system** _(:info/system)_
Displays system information for both the MCP server and the agent's client environment. Server information (OS, platform, hostname, Python version, working directory) is always shown. Client information (agent's OS, hostname, user, git remotes) requires the `allow-client-info` feature flag to be enabled.

### The `allow-client-info` Feature Flag

Client information collection is gated behind the `allow-client-info` feature flag due to privacy concerns. This flag is normally set globally (affects all projects) and defaults to false. It collects information about the agent's environment (OS, hostname, user) and requires explicit opt-in to respect user privacy. Ask the agent to set the `allow-client-info` feature flag to true to enable it.

## Project Management Commands

### Category Management

**@guide :project/category** _(:category)_
Shows category overview with list of current categories and available commands.

**@guide :project/category/list** _(:category/list)_
Lists all categories in the current project. Use `--verbose` for detailed information including directories and patterns.

**@guide :project/category/add** _(:category/add)_
Creates a new category for organising project content. Categories define directories and file patterns for content discovery.

**Examples:**
```
@guide :category/add docs
@guide :category/add docs --dir=documentation --patterns=README,CONTRIBUTING
@guide :category/add testing --description="Testing Guidelines"
```

**Parameters:**
- `name` (required) - Category name
- `--dir=<path>` - Directory path (defaults to category name)
- `--patterns=<patterns>` - Comma-separated file patterns (e.g., `README,CONTRIBUTING,test_`)
- `--description=<text>` - Human-readable description

**@guide :project/category/remove** _(:category/remove)_
Removes a category from the project.

**@guide :project/category/change** _(:category/change)_
Changes category properties.

**Examples:**
```
@guide :category/change docs --new-name=documentation
@guide :category/change docs --new-dir=doc --new-patterns=README,INSTALL
```

**@guide :project/category/update** _(:category/update)_
Updates category patterns incrementally without replacing all properties.

**Examples:**
```
@guide :category/update docs --add-patterns=CHANGELOG,AUTHORS
@guide :category/update docs --remove-patterns=old-file
```

**@guide :project/category/files** _(:category/files)_
Lists all files in a category directory.

### Collection Management

**@guide :project/collection** _(:collection)_
Shows collection overview with list of current collections and available commands.

**@guide :project/collection/list** _(:collection/list)_
Lists all collections in the current project. Use `--verbose` for detailed information including categories and descriptions.

**@guide :project/collection/add** _(:collection/add)_
Creates a new collection that groups multiple categories or other collections together.

**Examples:**
```
@guide :collection/add docs
@guide :collection/add api-docs --categories=code,examples
@guide :collection/add beginner --categories=docs,examples --description="Getting started content"
```

**Parameters:**
- `name` (required) - Collection name
- `--categories=<categories>` - Comma-separated category or collection names
- `--description=<text>` - Human-readable description

**@guide :project/collection/remove** _(:collection/remove)_
Removes a collection from the project.

**@guide :project/collection/change** _(:collection/change)_
Changes collection properties.

**Examples:**
```
@guide :collection/change docs --new-name=documentation
@guide :collection/change docs --new-categories=guide,lang,context
```

**@guide :project/collection/update** _(:collection/update)_
Updates collection categories incrementally.

**Examples:**
```
@guide :collection/update docs --add-categories=context
@guide :collection/update docs --remove-categories=old-category
```

Collections enable logical grouping of related content for easier access through the @guide prompt.

## Feature Flag Commands

### Project Flags

**@guide :flags/project**
Shows project flag overview and available commands.

**@guide :flags/project/list** _(:flags/project/list)_
Lists all project-specific feature flags. Use `--active` to show only active flags.

**@guide :flags/project/get** _(:flags/project/get)_
Gets the value of a specific project flag.

**Example:**
```
@guide :flags/project/get workflow
```

**@guide :flags/project/set** _(:flags/project/set)_
Sets a project-specific feature flag value.

**Examples:**
```
@guide :flags/project/set workflow
@guide :flags/project/set workflow false
@guide :flags/project/set content-style --value=mime
```

**@guide :flags/project/remove** _(:flags/project/remove)_
Removes a project-specific flag override, reverting to the feature flag value.

**Example:**
```
@guide :flags/project/remove workflow
```

### Feature Flags

**@guide :flags/feature**
Shows feature flag overview and available commands.

**@guide :flags/feature/list** _(:flags/feature/list)_
Lists all feature flags (apply across all projects). Use `--active` to show only active flags.

**@guide :flags/feature/get** _(:flags/feature/get)_
Gets the value of a specific feature flag.

**Example:**
```
@guide :flags/feature/get autoupdate
```

**@guide :flags/feature/set** _(:flags/feature/set)_
Sets a feature flag value.

**Examples:**
```
@guide :flags/feature/set workflow
@guide :flags/feature/set workflow false
@guide :flags/feature/set content-style --value=mime
```

**@guide :flags/feature/remove** _(:flags/feature/remove)_
Removes a feature flag.

**Example:**
```
@guide :flags/feature/remove autoupdate
```

### Available Flags

- **workflow** - Enable workflow phase tracking (Project and Feature)
- **openspec** - Enable OpenSpec integration (Project and Feature)
- **content-style** - Output format: None, plain, or mime (Project and Feature)
- **autoupdate** - Automatic content updates (Feature only)

## Filesystem Permissions

mcp-guide implements built-in security controls to ensure agent instructions don't transgress security boundaries outside the project.

### Security Model

**Read permissions:**
- Project directory: Always readable (default)
- Additional paths: Must be explicitly allowed via `additional_read_paths` in `.guide.yaml`
- System directories: Always blocked (e.g., `/etc`, `/System`, `C:\Windows`)

**Write permissions:**
- Controlled by `allowed_write_paths` in `.guide.yaml`
- Paths must be relative to project root
- Must end with trailing slash for directories (e.g., `src/`, `docs/`)
- Default: Empty list (no writes allowed outside explicit configuration)

**Temporary files:**
- Safe temp paths are allowed for read/write
- System validates temp directory safety

### Viewing Permissions

**@guide :project/perm** _(:perm)_
Shows current filesystem permissions configuration for the project - read permissions (project directory + additional paths) and write permissions (allowed write paths).

### Managing Permissions

Permissions are configured in `.guide.yaml`:

```yaml
allowed_write_paths:
  - src/
  - docs/

additional_read_paths:
  - /absolute/path/to/external/docs
```

**Write paths:**
- Must be relative to project root
- Must end with `/` for directories
- Examples: `src/`, `docs/`, `config.json`

**Read paths:**
- Must be absolute paths
- Cannot be system directories
- Examples: `/Users/name/external`, `/home/user/docs`

### Security Violations

When an agent attempts to read or write outside permitted paths, the operation is blocked, a `SecurityError` is raised, the violation is logged, and the agent receives an error message. This ensures that even if an agent is instructed to access restricted paths, the MCP server enforces security boundaries.

## Workflow Commands

When the `workflow` feature flag is enabled, additional workflow commands become available. See [Workflows](workflows.md) for complete documentation.

## OpenSpec Commands

When OpenSpec integration is enabled, OpenSpec commands provide access to spec-driven development features. See [OpenSpec Integration](openspec.md) for complete documentation.
