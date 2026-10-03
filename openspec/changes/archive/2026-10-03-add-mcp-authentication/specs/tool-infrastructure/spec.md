## ADDED Requirements

### Requirement: Automatic document updates remain available
The `update_documents` MCP tool SHALL retain its existing access behaviour
regardless of whether provider-backed policy is active. It supports automatic
document refresh when a caller starts a new MCP version and SHALL NOT require a
capability decision.

#### Scenario: Caller updates installed documents with provider active
- **WHEN** any remote caller invokes `update_documents` while a provider is
  active
- **THEN** the system SHALL apply the existing document-root resolution and
  update behaviour
