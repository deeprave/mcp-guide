# HTTPS Document Security Specification

## ADDED Requirements

### Requirement: Allowlist/Blocklist Configuration
The system SHALL support allowlist and blocklist configuration for HTTPS URLs at global and project levels.

#### Scenario: Allowlist mode
- **WHEN** allowlist is configured
- **THEN** only URLs in allowlist are permitted
- **AND** URLs in blocklist are denied even if in allowlist

#### Scenario: Blocklist mode
- **WHEN** blocklist is configured without allowlist
- **THEN** all URLs are permitted except those in blocklist

### Requirement: URL Validation Against Policy
The system SHALL validate HTTPS URLs against configured policy before fetching.

#### Scenario: URL allowed by policy
- **WHEN** URL passes allowlist/blocklist checks
- **THEN** fetch proceeds

#### Scenario: URL blocked by policy
- **WHEN** URL fails allowlist/blocklist checks
- **THEN** fetch is denied
- **AND** negative result is cached

### Requirement: Project-Level Policy Override
The system SHALL allow project-level policy to override global policy.

#### Scenario: Project policy override
- **WHEN** project has specific allowlist/blocklist
- **THEN** project policy takes precedence over global policy
- **AND** global policy is ignored for that project
