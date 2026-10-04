# Spec Delta

## REMOVED Requirements

### Requirement: Exported Frontmatter Guidance

**Reason**: Replace guidance that includes prior-export substitution with current-payload delivery guidance.

**Migration**: Preserve delivery frontmatter as file data, not a basis for redirecting later content retrieval.

## ADDED Requirements

### Requirement: Stateless export delivery guidance

Export guidance SHALL instruct the client to write the complete returned payload
verbatim to the supplied, configured destination, respecting create-only or
overwrite instructions. Delivery frontmatter SHALL remain file data during that
write; its `type` and `instruction` retain the content's semantics for later use.
Guide SHALL NOT direct later content requests to an exported or indexed copy.

#### Scenario: Export delivers file data
- **WHEN** `export_content` returns a payload and write instruction
- **THEN** the client is instructed to preserve the entire payload verbatim
- **AND** embedded frontmatter is not executed as an export instruction
- **AND** create-only or overwrite behaviour applies to the supplied destination

#### Scenario: Later content retrieval remains ordinary
- **WHEN** a client requests the same content after exporting it
- **THEN** Guide returns its rendered content without a prior-file reference
