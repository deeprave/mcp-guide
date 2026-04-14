# Commands

The `guide://` URI scheme provides the canonical command interface for direct access to MCP documents and functionality. Commands let you view project information, manage content, control workflows, and configure permissions. All commands follow a consistent structure with built-in help.

Prompt-style invocation may also be available in some clients, but this document uses `guide://` as the primary form. See [Guide URIs](guide-uris.md) for details.

**Note:** If your client supports prompts, equivalent forms like `@<prompt> :status` or `/<prompt> :status` may also work. The exact prompt name can vary.

## Command Structure

Commands are invoked with this syntax:

```
guide://_command[/args][?flags]
```

**Flag Syntax:**
Commands support two syntaxes for flags with values:
- `--flag=value` (always supported)
- `--flag value` (supported when flag is declared with `argrequired`)

**Examples:**
```
guide://_help
guide://_status
guide://_project
guide://_flags
guide://_create/category/docs
guide://_workflow/issue?tracking=MRP-177
guide://_flags/project/set/workflow?value=true
```

## Discovery with `guide://_help`

The `guide://_help` command resource is your primary discovery mechanism. Use it to explore available commands and their usage:

```
guide://_help              # Show all available commands grouped by category
guide://_help/flags        # Show detailed help for a specific command
```

**Recommended pattern:**
1. Start with `guide://_help` to see available commands
2. Use `guide://_help/<command>` for specific command usage
3. Execute the command
4. Use `guide://_help` again to discover related commands

## Core Information Commands

**`guide://_status`**
Shows system status and current project information including active project, workflow phase (if enabled), and OpenSpec integration status.

**`guide://_project`** _(:info/project, :project/info)_
Displays comprehensive project information including project name, categories, collections, feature flags, and filesystem permissions. Use `--verbose` or `-v` for detailed output including all category patterns.

**`guide://_flags`**
Shows all feature flags affecting the current project - feature flags (apply to all projects by default), project-specific flags (override feature flags), and resolved values (what the agent actually sees). Lists available flags with their scope restrictions (Project only, Feature only, or both).

**`guide://_system`** _(:info/system)_
Displays system information for both the MCP server and the agent's client environment. Server information (OS, platform, hostname, Python version, working directory) is always shown. Client information (agent's OS, hostname, user, git remotes) requires the `allow-client-info` feature flag to be enabled.

### The `allow-client-info` Feature Flag

Client information collection is gated behind the `allow-client-info` feature flag due to privacy concerns. This flag is normally set globally (affects all projects) and defaults to false. It collects information about the agent's environment (OS, hostname, user) and requires explicit opt-in to respect user privacy. Ask the agent to set the `allow-client-info` feature flag to true to enable it.

## Project Management Commands

### Category Management

**`guide://_project/category`** _(:category)_
Shows category overview with list of current categories and available commands.

**`guide://_project/category/list`** _(:category/list)_
Lists all categories in the current project. Use `--verbose` for detailed information including directories and patterns.

**`guide://_project/category/add`** _(:category/add)_
Creates a new category for organising project content. Categories define directories and file patterns for content discovery.

**Examples:**
```
guide://_category/add/docs
guide://_category/add/docs?dir=documentation&patterns=README,CONTRIBUTING
guide://_category/add/testing?description=Testing%20Guidelines
```

**Parameters:**
- `name` (required) - Category name
- `--dir=<path>` - Directory path (defaults to category name)
- `--patterns=<patterns>` - Comma-separated file patterns (e.g., `README,CONTRIBUTING,test_`)
- `--description=<text>` - Human-readable description

**`guide://_project/category/remove`** _(:category/remove)_
Removes a category from the project.

**`guide://_project/category/change`** _(:category/change)_
Changes category properties.

**Examples:**
```
guide://_category/change/docs?new-name=documentation
guide://_category/change/docs?new-dir=doc&new-patterns=README,INSTALL
```

**`guide://_project/category/update`** _(:category/update)_
Updates category patterns incrementally without replacing all properties.

**Examples:**
```
guide://_category/update/docs?add-patterns=CHANGELOG,AUTHORS
guide://_category/update/docs?remove-patterns=old-file
```

**`guide://_project/category/files`** _(:category/files)_
Lists all files in a category directory.

### Collection Management

**`guide://_project/collection`** _(:collection)_
Shows collection overview with list of current collections and available commands.

**`guide://_project/collection/list`** _(:collection/list)_
Lists all collections in the current project. Use `--verbose` for detailed information including categories and descriptions.

**`guide://_project/collection/add`** _(:collection/add)_
Creates a new collection that groups multiple categories or other collections together.

**Examples:**
```
guide://_collection/add/docs
guide://_collection/add/api-docs?categories=code,examples
guide://_collection/add/beginner?categories=docs,examples&description=Getting%20started%20content
```

**Parameters:**
- `name` (required) - Collection name
- `--categories=<categories>` - Comma-separated category or collection names
- `--description=<text>` - Human-readable description

**`guide://_project/collection/remove`** _(:collection/remove)_
Removes a collection from the project.

**`guide://_project/collection/change`** _(:collection/change)_
Changes collection properties.

**Examples:**
```
guide://_collection/change/docs?new-name=documentation
guide://_collection/change/docs?new-categories=guide,lang,context
```

**`guide://_project/collection/update`** _(:collection/update)_
Updates collection categories incrementally.

**Examples:**
```
guide://_collection/update/docs?add-categories=context
guide://_collection/update/docs?remove-categories=old-category
```

Collections enable logical grouping of related content for easier access through `guide://` expressions.

## Feature Flag Commands

### Project Flags

**`guide://_flags/project`**
Shows project flag overview and available commands.

**`guide://_flags/project/list`** _(:flags/project/list)_
Lists all project-specific feature flags. Use `--active` to show only active flags.

**`guide://_flags/project/get`** _(:flags/project/get)_
Gets the value of a specific project flag.

**Example:**
```
guide://_flags/project/get/workflow
```

**`guide://_flags/project/set`** _(:flags/project/set)_
Sets a project-specific feature flag value.

**Examples:**
```
guide://_flags/project/set/workflow
guide://_flags/project/set/workflow/false
guide://_flags/project/set/content-format?value=mime
```

**`guide://_flags/project/remove`** _(:flags/project/remove)_
Removes a project-specific flag override, reverting to the feature flag value.

**Example:**
```
guide://_flags/project/remove/workflow
```

### Feature Flags

**`guide://_flags/feature`**
Shows feature flag overview and available commands.

**`guide://_flags/feature/list`** _(:flags/feature/list)_
Lists all feature flags (apply across all projects). Use `--active` to show only active flags.

**`guide://_flags/feature/get`** _(:flags/feature/get)_
Gets the value of a specific feature flag.

**Example:**
```
guide://_flags/feature/get/autoupdate
```

**`guide://_flags/feature/set`** _(:flags/feature/set)_
Sets a feature flag value.

**Examples:**
```
guide://_flags/feature/set/workflow
guide://_flags/feature/set/workflow/false
guide://_flags/feature/set/content-format?value=mime
```

**`guide://_flags/feature/remove`** _(:flags/feature/remove)_
Removes a feature flag.

**Example:**
```
guide://_flags/feature/remove/autoupdate
```

### Available Flags

- **workflow** - Enable workflow phase tracking (Project and Feature)
- **openspec** - Enable OpenSpec integration (Project and Feature)
- **content-style** - Markdown formatting: plain, headings, or full (Project and Feature)
- **content-format** - Content MIME type: text or mime (Project and Feature)
- **autoupdate** - Automatic content updates (Feature only)

## Document Commands

Document commands let you manage stored documents — content that lives in the document store rather than as files on disk. See [Stored Documents](stored-documents.md) for the full picture.

**`guide://_document`**
Shows available document commands.

**`guide://_document/add`** _`<category> <path>`_
Adds a local file to the document store in the specified category.

**Examples:**
```
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?as=custom-name
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?force
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?agent-instruction
```

**`guide://_document/add-url`** _`<category> <url>`_
Fetches content from a URL and stores it in the specified category.

**Examples:**
```
guide://_document/add-url/docs/https%3A%2F%2Fexample.com%2Fapi-reference
guide://_document/add-url/docs/https%3A%2F%2Fexample.com%2Fguide?as=api-guide
```

**`guide://_document/list`** _`<category>`_
Lists stored documents in a category.

**`guide://_document/show`** _`<category> <name>`_
Displays the content of a stored document.

**`guide://_document/update`** _`<category> <name>`_
Updates a stored document's name, category, or metadata.

**`guide://_document/remove`** _`<category> <name>`_
Removes a stored document from a category.

## Export Commands

Export commands manage tracked content exports — rendered content saved to files for knowledge persistence. See [Content Management](content-management.md) for how exports work.

**`guide://_export/add`** _`<expression> <path>`_
Exports rendered content to a file and tracks it.

**Examples:**
```
guide://_export/add/docs/documentation.md
guide://_export/add/architecture/arch.md?force
```

**`guide://_export/list`**
Lists all tracked exports with their expression, path, and staleness status.

**`guide://_export/remove`** _`<expression>`_
Removes an export tracking entry (does not delete the exported file).

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

**`guide://_project/perm`** _(:perm)_
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
- Can be specific files or directories (end with `/` for directories)
- Examples: `src/`, `docs/`, `config.json`, `.guide.yaml`

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
