## ADDED Requirements

### Requirement: Cache frontmatter preservation
The frontmatter processor SHALL parse the `cache` field for cache-policy resolution while continuing to strip frontmatter from delivered document content.

#### Scenario: Cache field does not leak into content
- **WHEN** a hosted document includes a valid `cache` frontmatter field
- **THEN** the rendered body excludes the frontmatter
- **AND** cache-policy resolution receives the parsed field
