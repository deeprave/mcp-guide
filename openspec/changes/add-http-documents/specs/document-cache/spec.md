# Document Cache Specification

## ADDED Requirements

### Requirement: Session-Based Cache
The system SHALL maintain an in-memory cache of documents per session.

#### Scenario: Cache document content
- **WHEN** document is successfully retrieved
- **THEN** content is cached with hash key
- **AND** cache persists for session duration

#### Scenario: Cache negative result
- **WHEN** document is not found or fails permanently
- **THEN** negative result is cached with hash key
- **AND** prevents repeated failed requests

### Requirement: Cache Invalidation
The system SHALL invalidate cache when session ends or project switches.

#### Scenario: Session end cache clear
- **WHEN** session ends
- **THEN** all cached documents are evicted

#### Scenario: Project switch cache clear
- **WHEN** project is switched
- **THEN** all cached documents are evicted

### Requirement: Optional Persistent Cache
The system SHALL support optional persistent cache in XDG_CACHE directory for cross-session reuse.

#### Scenario: Persistent cache hit
- **WHEN** document is in persistent cache
- **THEN** content is loaded from cache
- **AND** hash key ensures unambiguous reference

**Note:** This cache is shared between client documents (`add-client-documents`) and HTTPS documents (`add-http-documents`). Whichever change is implemented first creates this capability.
