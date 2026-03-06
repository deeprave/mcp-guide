## ADDED Requirements

### Requirement: Project Category Commands
The system SHALL provide individual command templates under `project/category/` for managing categories.

#### Scenario: List categories
- **GIVEN** a project with categories
- **WHEN** user invokes `:project/category/list` or `:category/list`
- **THEN** call `category_list` tool with `CategoryListArgs(verbose=False)`

#### Scenario: List categories verbose
- **GIVEN** a project with categories
- **WHEN** user invokes `:project/category/list --verbose`
- **THEN** call `category_list` tool with `CategoryListArgs(verbose=True)`

#### Scenario: Add category
- **GIVEN** a project configuration
- **WHEN** user invokes `:project/category/add docs --dir=documentation`
- **THEN** call `category_add` tool with `CategoryAddArgs(name="docs", dir="documentation")`

#### Scenario: Remove category
- **GIVEN** a category exists
- **WHEN** user invokes `:project/category/remove docs`
- **THEN** call `category_remove` tool with `CategoryRemoveArgs(name="docs")`

#### Scenario: Change category
- **GIVEN** a category exists
- **WHEN** user invokes `:project/category/change docs --new-name=documentation`
- **THEN** call `category_change` tool with `CategoryChangeArgs(name="docs", new_name="documentation")`

#### Scenario: Update category patterns
- **GIVEN** a category exists
- **WHEN** user invokes `:project/category/update docs --add-patterns=CHANGELOG`
- **THEN** call `category_update` tool with `CategoryUpdateArgs(name="docs", add_patterns=["CHANGELOG"])`

#### Scenario: List category files
- **GIVEN** a category exists
- **WHEN** user invokes `:project/category/files docs`
- **THEN** call `category_list_files` tool with `CategoryListFilesArgs(name="docs")`

#### Scenario: Category overview
- **GIVEN** a project with categories
- **WHEN** user invokes `:project/category` or `:category`
- **THEN** display category help with list of current categories

### Requirement: Project Collection Commands
The system SHALL provide individual command templates under `project/collection/` for managing collections.

#### Scenario: List collections
- **GIVEN** a project with collections
- **WHEN** user invokes `:project/collection/list` or `:collection/list`
- **THEN** call `collection_list` tool with `CollectionListArgs(verbose=False)`

#### Scenario: List collections verbose
- **GIVEN** a project with collections
- **WHEN** user invokes `:project/collection/list --verbose`
- **THEN** call `collection_list` tool with `CollectionListArgs(verbose=True)`

#### Scenario: Add collection
- **GIVEN** a project configuration
- **WHEN** user invokes `:project/collection/add getting-started --categories=docs,guide`
- **THEN** call `collection_add` tool with `CollectionAddArgs(name="getting-started", categories=["docs", "guide"])`

#### Scenario: Remove collection
- **GIVEN** a collection exists
- **WHEN** user invokes `:project/collection/remove getting-started`
- **THEN** call `collection_remove` tool with `CollectionRemoveArgs(name="getting-started")`

#### Scenario: Change collection
- **GIVEN** a collection exists
- **WHEN** user invokes `:project/collection/change getting-started --new-name=quickstart`
- **THEN** call `collection_change` tool with `CollectionChangeArgs(name="getting-started", new_name="quickstart")`

#### Scenario: Update collection categories
- **GIVEN** a collection exists
- **WHEN** user invokes `:project/collection/update getting-started --add-categories=context`
- **THEN** call `collection_update` tool with `CollectionUpdateArgs(name="getting-started", add_categories=["context"])`

#### Scenario: Collection overview
- **GIVEN** a project with collections
- **WHEN** user invokes `:project/collection` or `:collection`
- **THEN** display collection help with list of current collections

### Requirement: Command Flag Syntax
The system SHALL use `--flag=value` syntax for all command arguments with values.

#### Scenario: Value flags
- **GIVEN** a command accepting flags
- **WHEN** user provides `--dir=path` or `--patterns=README,CHANGELOG`
- **THEN** parse as `kwargs.dir = "path"` or `kwargs.patterns = "README,CHANGELOG"`

#### Scenario: Boolean flags
- **GIVEN** a command accepting flags
- **WHEN** user provides `--verbose` or `-v`
- **THEN** parse as `kwargs.verbose = True`

#### Scenario: Usage examples
- **GIVEN** command template error messages
- **WHEN** displaying usage
- **THEN** show `--flag=value` syntax, not `--flag value`

### Requirement: Command Aliases
The system SHALL provide short aliases for common command paths.

#### Scenario: Category alias
- **GIVEN** category commands
- **WHEN** user invokes `:category` or `:category/list`
- **THEN** resolve to `:project/category` or `:project/category/list`

#### Scenario: Collection alias
- **GIVEN** collection commands
- **WHEN** user invokes `:collection` or `:collection/add`
- **THEN** resolve to `:project/collection` or `:project/collection/add`

### Requirement: Project Info Command
The system SHALL provide a `project/info` command that displays project information.

#### Scenario: Show project info
- **GIVEN** a current project
- **WHEN** user invokes `project/info`
- **THEN** display project information (same as old `info/project`)

#### Scenario: Alias support
- **GIVEN** backward compatibility needed
- **WHEN** user invokes `info/project`
- **THEN** redirect to `project/info` command

### Requirement: Project Permission Command
The system SHALL provide a `project/perm` command that accepts action-first syntax to manage file permissions.

#### Scenario: Add write permission
- **GIVEN** a file path
- **WHEN** user invokes `project/perm add myfile.txt write`
- **THEN** add write permission to file

#### Scenario: Add read permission
- **GIVEN** a file path
- **WHEN** user invokes `project/perm add myfile.txt read`
- **THEN** add read permission to file

#### Scenario: Delete permissions
- **GIVEN** a file with permissions
- **WHEN** user invokes `project/perm del myfile.txt [read|write]`
- **THEN** remove specified permission from file

## MODIFIED Requirements

### Requirement: Command Template Organization
The system SHALL organize project management commands under `project/*` namespace.

#### Scenario: Namespace structure
- **GIVEN** command template system
- **WHEN** organizing templates
- **THEN** place category, collection, info, perm under `_commands/project/`
- **AND** maintain consistent action-first syntax

## REMOVED Requirements

### Requirement: Create Namespace Commands
**Reason**: Non-intuitive namespace, replaced with action-first syntax under `project/*`
**Migration**: Use `project/category add` and `project/collection add` instead

The following commands are removed:
- `create/category` → `project/category add`
- `create/collection` → `project/collection add`

### Requirement: Top-Level Permission Commands
**Reason**: Consolidated under `project/perm` namespace
**Migration**: Use `project/perm [action]` instead

The following commands are removed:
- `perm/write-add` → `project/perm add [file] write`
- `perm/read-add` → `project/perm add [file] read`
- `perm/write-del` → `project/perm del [file] write`
- `perm/read-del` → `project/perm del [file] read`
