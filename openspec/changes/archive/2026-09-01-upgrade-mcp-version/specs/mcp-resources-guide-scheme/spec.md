## ADDED Requirements

### Requirement: Request-Scoped Guide URI Resolution
The server SHALL obtain the requested `guide://` URI through the framework-neutral
resource request context. Resource resolution SHALL NOT depend on the internal shape
of a FastMCP request-context object.

The advertised Guide resource templates SHALL include an optional RFC 6570
`session_id` query variable. A native `resources/read` request with
`?session_id=<id>` SHALL pass that value through the same validated Session resolver
used by the shared tool-argument contract before content rendering or command
execution. It SHALL use the value as an opaque FastMCP Session ID, not a
Guide-generated or separately mapped identifier.

When a retained handshake-era resource request omits the query variable, the adapter
SHALL use the public FastMCP connection `session_id` as the defined legacy fallback.
For a modern request, omitting the query variable SHALL not create replacement
cross-request state; a project-bound resource SHALL return the defined unbound
guidance unless another defined bootstrap applies.

#### Scenario: Guide content resource request
- **WHEN** a client reads a `guide://{collection}/{document}{?session_id}` resource through a negotiated modern request
- **THEN** the resource handler SHALL obtain the URI from the application request context
- **AND** it SHALL resolve the validated query `session_id` through the same request
  Session resolver as a tool call
- **AND** it SHALL delegate content resolution using the resulting project identity

#### Scenario: Session-sensitive template is read natively
- **WHEN** a resource template whose rendering depends on Session data is read with a
  valid `session_id` query value
- **THEN** its rendering SHALL observe the same bound Session state as
  `guide.read_resource` given that Session ID
- **AND** it SHALL not render using ambient process, global, or unrelated connection
  state

#### Scenario: Guide command resource request
- **WHEN** a client reads an underscore-prefixed
  `guide://_{command_path*}{?session_id}` command URI
- **THEN** the command parser SHALL receive the URI and request context through the resource adapter
- **AND** embedded response instructions SHALL be preserved in the protocol result

#### Scenario: Resource session identifier is unsafe
- **WHEN** a resource URI supplies an empty, overlong, or control-character-bearing
  `session_id` query value
- **THEN** the shared resolver SHALL reject it before Session lookup
- **AND** it SHALL not create a runtime Session entry or include the raw value in a
  user-visible diagnostic
