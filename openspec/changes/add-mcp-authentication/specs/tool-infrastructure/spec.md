## ADDED Requirements

### Requirement: Document-update authorisation
When provider-backed policy is active for a remote caller, the
`update_documents` MCP tool SHALL require the `admin` scope before it resolves
or modifies the installed document root. When no provider is selected, remote
callers SHALL retain existing behaviour. Stdio callers SHALL retain unrestricted
access to the tool.

#### Scenario: Admin updates installed documents
- **WHEN** an `admin`-scoped caller invokes `update_documents`
- **THEN** the system SHALL apply the existing document-root resolution and
  update behaviour

#### Scenario: Caller without admin scope requests a document update
- **WHEN** an unauthenticated or non-admin caller invokes `update_documents`
- **THEN** the system SHALL return an authorisation failure
- **AND** it SHALL not resolve or modify the document root
