## Purpose

Define requirements for content-oriented tools and related guidance exposed through the system.
## Requirements
### Requirement: Stateless content export

`export_content` SHALL return the current rendered content for an expression
with its resolved disposition and instruction as export frontmatter. The caller
SHALL supply a client-owned destination; Guide SHALL validate that destination
against configured write permissions without writing the file, adding
permissions, or retaining an export record.

#### Scenario: Export returns rendered content and metadata

- **WHEN** a caller exports content with resolved disposition or instruction
- **THEN** the returned payload contains that metadata as frontmatter before the
  current rendered content

#### Scenario: Client-owned destination is permitted

- **WHEN** a caller supplies a destination covered by configured write paths
- **THEN** Guide returns the export payload and canonicalised destination
- **AND** it does not write the destination or persist export state

#### Scenario: Unsafe or unpermitted destination is rejected

- **WHEN** a caller supplies a destination outside configured write paths or
  containing instruction-breaking characters
- **THEN** Guide rejects the export without returning a write instruction
