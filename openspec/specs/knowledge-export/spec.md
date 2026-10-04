# knowledge-export Specification

## Purpose
Define exported-content metadata so files retain their resolved delivery semantics.

## Requirements

### Requirement: Exported Content Frontmatter

The `export_content` tool SHALL prepend YAML frontmatter to the payload it
returns so a client can preserve the resolved content semantics if it chooses to
write or index that payload. The export operation SHALL not persist an export
destination, timestamp, source metadata hash, or any other export record in
the Guide project.

The exported frontmatter SHALL include:
- `type`: the resolved exported content type
- `instruction`: the resolved exported instruction

The exported payload beneath that frontmatter SHALL remain the same rendered
content that `export_content` would otherwise return for the active content
format.

#### Scenario: Single document export preserves explicit metadata
- **WHEN** `export_content` exports a single document with resolved type and instruction metadata
- **THEN** the exported content begins with YAML frontmatter
- **AND** the frontmatter contains the resolved `type`
- **AND** the frontmatter contains the resolved `instruction`
- **AND** the rendered body follows after the frontmatter

#### Scenario: Export type defaults to user information
- **WHEN** all collected documents resolve to `user/information`
- **THEN** the exported frontmatter `type` is `user/information`

#### Scenario: Agent information outranks user information
- **WHEN** at least one collected document resolves to `agent/information`
- **AND** no collected document resolves to `agent/instruction`
- **THEN** the exported frontmatter `type` is `agent/information`

#### Scenario: Agent instruction outranks all other types
- **WHEN** at least one collected document resolves to `agent/instruction`
- **THEN** the exported frontmatter `type` is `agent/instruction`

#### Scenario: Export instruction reuses existing multi-document resolution
- **WHEN** `export_content` exports multiple collected documents
- **THEN** the exported frontmatter `instruction` is resolved using the existing instruction handling strategy
- **AND** duplicate instruction content is removed
- **AND** important instruction handling is preserved

#### Scenario: Export preserves rendered payload format
- **WHEN** `export_content` renders content using the active content-format setting
- **THEN** the rendered payload beneath the export frontmatter preserves that format
- **AND** adding export frontmatter does not change the selected body format

#### Scenario: Export does not alter Guide project state
- **WHEN** a client requests an export
- **THEN** Guide returns the rendered export payload without modifying the bound project's configuration or write permissions
- **AND** later content retrieval returns Guide-rendered content rather than a reference to that client-side export

### Requirement: Client-owned export destination

`export_content` SHALL treat its requested destination as client-owned output
information. Guide SHALL canonicalise backslash separators to forward slashes
and use that same destination for validation and client delivery, without
inferring the client platform from the server. It SHALL not resolve a default destination, select an agent-specific knowledge
directory, or claim that it created or controls the file. Before returning an
export hand-off, Guide SHALL require the supplied destination to be covered by
the project's configured `allowed_write_paths`. It SHALL reject an uncovered
destination rather than adding permissions. This check SHALL NOT inspect or
resolve paths against the server's filesystem as a proxy for the client's
filesystem.

Configured write entries SHALL NOT designate a filesystem root, including
lexically equivalent roots, Windows drive roots or UNC share roots. Export
destinations SHALL NOT contain ASCII control characters (U+0000–U+001F and
U+007F) or backticks. Destination validation failures SHALL return a fixed
security error without reproducing the rejected destination in the response.
Export commands, including aliases through prompt and resource routes, SHALL
apply the same unsafe-character rejection before rendering agent-facing guidance.

#### Scenario: A filesystem root is requested as a write entry
- **WHEN** project configuration or a permission addition supplies a filesystem-root write entry or its lexical equivalent
- **THEN** Guide rejects the entry without saving changed permissions

#### Scenario: Destination contains instruction-breaking characters
- **WHEN** an export destination contains an ASCII control character or backtick, whether or not it is within a configured directory
- **THEN** Guide rejects the export before returning content or a write instruction
- **AND** the security failure does not reproduce the rejected destination

#### Scenario: Client selects an export destination
- **WHEN** a client supplies an export destination
- **THEN** Guide returns that destination with backslashes canonicalised to forward slashes with the export payload
- **AND** the client remains responsible for deciding whether and how to write or index the payload

#### Scenario: Export command destination contains instruction-breaking characters
- **WHEN** a prompt or resource invokes an export command or alias with ASCII controls or backticks in its destination
- **THEN** Guide returns a fixed security failure before rendering the command guidance
- **AND** the failure does not reproduce the rejected destination

#### Scenario: Export destination uses backslash separators
- **WHEN** an export destination uses backslash separators and its forward-slash form is covered by configured write paths
- **THEN** Guide validates that forward-slash form and uses the same form in the client write instruction

#### Scenario: Destination is outside configured write paths
- **WHEN** the requested export destination is not covered by a configured write-path entry
- **THEN** Guide rejects the export and returns no instruction to write that destination
- **AND** it does not add the destination or modify project configuration

#### Scenario: Destination is covered by a configured file or directory
- **WHEN** the requested destination matches a configured file entry or is within a configured write directory
- **THEN** Guide can return the export payload and destination
- **AND** the existing permissions remain unchanged

#### Scenario: Temporary destination is not implicitly permitted
- **WHEN** an export destination is a temporary location not covered by configured write paths
- **THEN** Guide rejects it even if the general write policy permits temporary locations

#### Scenario: Authentication does not bypass destination validation
- **WHEN** an authenticated admin requests an export outside configured write paths
- **THEN** Guide rejects the destination without changing permissions

### Requirement: No substitution of prior exports for Guide content

For an equivalent expression and pattern, `get_content` and content URI reads
SHALL return Guide-rendered content rather than a reference to a prior export.
Active tool descriptions, result instructions, templates, command guidance,
documentation and examples SHALL NOT direct the client to use a tracked or
indexed export in place of obtaining that content from Guide. Metadata-based
skip, staleness and cache-bypass guidance SHALL be retired. Export delivery
frontmatter and instructions for the client to write the current export payload
SHALL remain distinct from retired export-reuse behaviour.

#### Scenario: Export is followed by equivalent content retrieval
- **WHEN** a client exports an expression and then requests the same expression and pattern through `get_content` or an equivalent content URI
- **THEN** Guide returns its rendered content using ordinary retrieval semantics
- **AND** it does not direct the client to read or index the earlier export instead

#### Scenario: Legacy tracking cannot redirect content retrieval
- **WHEN** a loaded project previously contained a tracked export for the requested expression
- **THEN** content retrieval does not return an export path or prior-export instruction

#### Scenario: Export guidance remains independent of tracking
- **WHEN** Guide returns instructions for a current export
- **THEN** those instructions concern the returned payload and permitted destination
- **AND** they do not depend on a remembered destination, timestamp or source hash

### Requirement: Export tracking interface retirement

Guide SHALL not expose persistent export tracking through tools, commands, or
project configuration. Legacy `exports` entries encountered in existing project
configuration SHALL be ignored and SHALL not be written when that configuration
is subsequently saved.

#### Scenario: Existing configuration contains tracked exports
- **WHEN** Guide loads a project configuration containing legacy `exports` data
- **THEN** it accepts the remaining project configuration
- **AND** it does not use the legacy export data to alter content delivery
- **AND** a later save omits the legacy export data

#### Scenario: Client requests retired export tracking
- **WHEN** a client discovers Guide's tools or commands
- **THEN** `list_exports`, `remove_export`, `guide://_export/list`, and `guide://_export/remove` are absent
