## ADDED Requirements

### Requirement: Response metadata adaptation
The common response adapters SHALL accept resolved Guide response metadata separately from a Guide Result and serialise its side-band fields through `_meta` without changing the canonical structured result payload.

#### Scenario: Metadata and structured content are independent
- **WHEN** an adapter receives a result and side-band response metadata
- **THEN** the native response includes the metadata in `_meta`
- **AND** its structured content represents only the result
