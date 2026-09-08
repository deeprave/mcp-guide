## ADDED Requirements

### Requirement: Bounded stored document content

The document store SHALL validate UTF-8 content byte length before committing an
add or replacement. It SHALL query stored byte size before materialising a
document body. In both cases an oversized body SHALL fail with
`max_size_exceeded`, preserving any existing replacement target.

#### Scenario: Oversized replacement preserves existing content
- **WHEN** a replacement exceeds the configured content limit
- **THEN** the operation fails before commit
- **AND** the previous body remains unchanged
