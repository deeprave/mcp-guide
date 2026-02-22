## ADDED Requirements

### Requirement: Project Category Command
The system SHALL provide a `project/category` command that accepts action-first syntax to manage categories.

#### Scenario: List categories
- **GIVEN** a project with categories
- **WHEN** user invokes `project/category list`
- **THEN** call `category` tool with `CategoryListArgs(action="list")`

#### Scenario: Add category
- **GIVEN** a project configuration
- **WHEN** user invokes `project/category add docs`
- **THEN** call `category` tool with `CategoryAddArgs(action="add", name="docs")`

#### Scenario: Remove category
- **GIVEN** a category exists
- **WHEN** user invokes `project/category remove docs`
- **THEN** call `category` tool with `CategoryRemoveArgs(action="remove", name="docs")`

#### Scenario: Other actions
- **GIVEN** appropriate context
- **WHEN** user invokes `project/category [change|update|files] [name] [args]`
- **THEN** call `category` tool with appropriate Args class

### Requirement: Project Collection Command
The system SHALL provide a `project/collection` command that accepts action-first syntax to manage collections.

#### Scenario: List collections
- **GIVEN** a project with collections
- **WHEN** user invokes `project/collection list`
- **THEN** call `collection` tool with `CollectionListArgs(action="list")`

#### Scenario: Add collection
- **GIVEN** a project configuration
- **WHEN** user invokes `project/collection add getting-started`
- **THEN** call `collection` tool with `CollectionAddArgs(action="add", name="getting-started")`

#### Scenario: Other actions
- **GIVEN** appropriate context
- **WHEN** user invokes `project/collection [remove|change|update] [name] [args]`
- **THEN** call `collection` tool with appropriate Args class

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
