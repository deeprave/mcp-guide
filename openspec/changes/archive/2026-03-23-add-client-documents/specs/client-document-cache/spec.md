# Client Document Cache Specification

**Dependencies:** `filesystem-interaction` (uses `send_file_content`)

## ADDED Requirements

### Requirement: Session-Based Cache
The system SHALL maintain an in-memory cache of client documents per session.

#### Scenario: Cache client document content
- **WHEN** client document is successfully retrieved
- **THEN** content is cached with full path hash as key
- **AND** cache persists for session duration

#### Scenario: Cache negative result
- **WHEN** client document is not found or fails validation
- **THEN** negative result is cached with full path hash as key
- **AND** prevents repeated failed requests

### Requirement: Cache Invalidation
The system SHALL invalidate cache when session ends or project switches.

#### Scenario: Session end cache clear
- **WHEN** session ends
- **THEN** all cached client documents are evicted

#### Scenario: Project switch cache clear
- **WHEN** project is switched
- **THEN** all cached client documents are evicted

### Requirement: Optional Persistent Cache
The system SHALL support optional persistent cache in XDG_CACHE directory for cross-project reuse.

#### Scenario: Persistent cache hit
- **WHEN** client document is in persistent cache
- **THEN** content is loaded from cache
- **AND** full path hash ensures unambiguous reference
