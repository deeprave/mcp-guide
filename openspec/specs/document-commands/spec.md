# document-commands Specification

## Purpose
TBD - created by archiving change add-documents. Update Purpose after archive.
## Requirements
### Requirement: Document Command Templates

The system SHALL provide prompt command templates in `_commands/document/` for managing stored documents via the agent.

#### Scenario: Parent command summary
- **WHEN** user invokes `:document`
- **THEN** display available document subcommands (add, remove, list)

### Requirement: Document Add Command

The system SHALL provide a `:document/add` command that instructs the agent to ingest a local file into the document store via `send_file_content`.

Required arguments:
- `category` — target category (must exist)
- `path` — path to the local file to import

Optional arguments:
- `--as <name>` — override the stored document name (default: basename of path)
- `--force` — overwrite existing document regardless of mtime
- `--metadata <object>` — arbitrary key-value metadata to attach to the document
- `--agent-info` — set document type to `agent/information`
- `--agent-instruction` — set document type to `agent/instruction` (the default)
- `--user-info` — set document type to `user/information`

The type flags (`--agent-info`, `--agent-instruction`, `--user-info`) are mutually exclusive. If multiple are specified, the last one wins.

The `send_file_content` MCP tool SHALL accept an optional `metadata` parameter (dict) which is merged with any frontmatter metadata parsed from the file content.

The command SHALL instruct the agent to:
1. Read the file content and mtime from the specified path
2. Call `send_file_content` with the file content, path, category, name, mtime, type, and metadata
3. Include force flag if specified
4. Parse the `--metadata` value into a dict before passing to the tool

#### Scenario: Add a document with defaults
- **WHEN** user invokes `:document/add docs /path/to/file.md`
- **THEN** agent reads the file and calls send_file_content with category=docs, name derived from basename, type=agent/instruction

#### Scenario: Add a document with name override
- **WHEN** user invokes `:document/add docs /path/to/file.md --as guide.md`
- **THEN** agent calls send_file_content with name=guide.md

#### Scenario: Force overwrite
- **WHEN** user invokes `:document/add docs /path/to/file.md --force`
- **THEN** agent calls send_file_content with force=true

#### Scenario: Add with metadata
- **WHEN** user invokes `:document/add docs /path/to/file.md --metadata '{requires-workflow: true}'`
- **THEN** agent parses the metadata string into a dict and calls send_file_content with metadata={"requires-workflow": true}

#### Scenario: Add with document type
- **WHEN** user invokes `:document/add docs /path/to/file.md --user-info`
- **THEN** agent calls send_file_content with type=user/information

#### Scenario: Metadata merges with frontmatter
- **WHEN** a file has frontmatter metadata and `--metadata` is also provided
- **THEN** the event metadata from `--metadata` takes precedence over frontmatter values for overlapping keys

### Requirement: Document Remove Command

The system SHALL provide a `:document/remove` command that instructs the agent to remove a stored document using the `document_remove` tool.

Required arguments:
- `category` — category containing the document
- `name` — document name to remove

#### Scenario: Remove a document
- **WHEN** user invokes `:document/remove docs guide.md`
- **THEN** agent calls document_remove with category=docs, name=guide.md

### Requirement: Document List Command

The system SHALL provide a `:document/list` command that instructs the agent to list stored documents in a category using `category_list_files` with source filter `stored`.

Required arguments:
- `category` — category name to list documents from

#### Scenario: List stored documents
- **WHEN** user invokes `:document/list docs`
- **THEN** agent calls category_list_files with category=docs, source=stored

