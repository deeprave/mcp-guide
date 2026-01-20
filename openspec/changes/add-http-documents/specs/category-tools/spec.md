# Category Tools Specification

## MODIFIED Requirements

### Requirement: Category HTTPS Document Patterns
The Category model SHALL support an `https` dict mapping patterns to lists of HTTPS URLs.

#### Scenario: Add category with HTTPS patterns
- **WHEN** category is created with `https={"*.md": ["https://example.com/doc1.md", "https://example.com/doc2.md"]}`
- **THEN** category stores HTTPS pattern mappings
- **AND** patterns support glob syntax
- **AND** URLs are explicit (no globs in URLs)

### Requirement: HTTPS-Only Enforcement
The system SHALL reject HTTP URLs and only accept HTTPS URLs.

#### Scenario: Add HTTPS URL
- **WHEN** URL starts with `https://`
- **THEN** URL is accepted

#### Scenario: Reject HTTP URL
- **WHEN** URL starts with `http://`
- **THEN** system rejects URL with error
