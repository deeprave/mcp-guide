## ADDED Requirements

### Requirement: Request-Scoped Guide URI Resolution
The server SHALL obtain the requested `guide://` URI through the framework-neutral
resource request context. Resource resolution SHALL NOT depend on the internal shape
of a FastMCP request-context object.

#### Scenario: Guide content resource request
- **WHEN** a client reads a `guide://{collection}/{document}` resource through a negotiated modern request
- **THEN** the resource handler SHALL obtain the URI from the application request context
- **AND** it SHALL delegate content resolution using the project identity from that same context

#### Scenario: Guide command resource request
- **WHEN** a client reads an underscore-prefixed `guide://` command URI
- **THEN** the command parser SHALL receive the URI and request context through the resource adapter
- **AND** embedded response instructions SHALL be preserved in the protocol result
