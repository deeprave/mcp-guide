# http-documents Specification

## Purpose
TBD - created by archiving change add-documents. Update Purpose after archive.
## Requirements
### Requirement: Document Add URL Command

The system SHALL provide a `:document/add-url` command template that instructs the agent to fetch content from a URL, convert it to markdown, and ingest it via `send_file_content`.

#### Scenario: Fetch and ingest URL with default type
- **WHEN** the agent receives `:document/add-url <category> <url>`
- **THEN** the agent SHALL fetch the URL content, requesting markdown format where available
- **AND** convert to markdown if the response is not already markdown
- **AND** the translation style SHALL be concise and AI-friendly (agent/information default)
- **AND** call `send_file_content` with `source=<url>`, triggering `source_type="url"` derivation
- **AND** extract `Last-Modified` header as mtime epoch float, falling back to current timestamp

#### Scenario: Translation style varies by document type
- **WHEN** `--agent-instruction` is specified
- **THEN** the markdown translation SHALL be concise, succinct, and framed as directives
- **WHEN** `--agent-info` is specified or no type flag is given
- **THEN** the markdown translation SHALL be concise, capturing all points, suitable for AI consumption
- **WHEN** `--user-info` is specified
- **THEN** the markdown translation SHALL prioritise readability, fluidity, and clarity for human consumption

#### Scenario: mtime from HTTP headers
- **WHEN** the HTTP response includes a `Last-Modified` header
- **THEN** the agent SHALL parse it as epoch float and pass as `mtime` to `send_file_content`
- **WHEN** no `Last-Modified` header is present
- **THEN** the agent SHALL use the current timestamp as `mtime`

#### Scenario: Custom document name
- **WHEN** `--as <name>` is specified
- **THEN** the document SHALL be stored with that name instead of the URL-derived default

#### Scenario: Force overwrite
- **WHEN** `--force` is specified
- **THEN** the document SHALL be ingested regardless of existing mtime

