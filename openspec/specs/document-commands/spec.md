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

The `:document/add` command SHALL support a handoff-capable execution path for clients that expose `agent.has_handoff`, while retaining a universal inline fallback path.

The command SHALL continue to preserve the same `send_file_content` semantics and argument handling as the existing command.

#### Scenario: Handoff-capable client uses separate execution
- **WHEN** `:document/add` is rendered for a client with `agent.has_handoff=true`
- **THEN** the template instructs the agent to use separate execution when it can still complete the workflow end-to-end
- **AND** the workflow still ends with `send_file_content`

#### Scenario: Inline fallback remains universal
- **WHEN** `:document/add` is rendered for a client with `agent.has_handoff=false`
- **THEN** the template instructs the agent to perform the workflow inline

#### Scenario: Standardized fallback wording
- **WHEN** the handoff-oriented path cannot actually be used
- **THEN** the agent uses standardized fallback explanation wording before continuing inline

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

