## ADDED Requirements

### Requirement: Export authorisation
For HTTP(S) callers, the `export_content` tool SHALL require the `admin` scope
before it reads and returns exported document content. Stdio callers SHALL
retain unrestricted export access. Existing exported frontmatter and rendering
behaviour SHALL remain unchanged for authorised callers.

#### Scenario: Admin exports content
- **WHEN** an `admin`-scoped caller invokes `export_content`
- **THEN** the system SHALL produce the existing authorised export result,
  including required frontmatter and rendered content

#### Scenario: Caller without admin scope requests an export
- **WHEN** an unauthenticated or non-admin caller invokes `export_content`
- **THEN** the system SHALL return an authorisation failure
- **AND** it SHALL not return exported document content
