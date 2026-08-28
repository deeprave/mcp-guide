## ADDED Requirements

### Requirement: Modern Tool Result Adaptation
The system SHALL convert internal tool `Result` values into SDK-native MCP tool
responses through one protocol adapter. The adapter SHALL preserve result content,
error status, `instruction`, and `additional_agent_instructions` semantics while
placing protocol metadata in the modern response structure.

#### Scenario: Successful tool result
- **WHEN** a tool returns a successful internal result
- **THEN** the protocol adapter SHALL emit a modern tool response with equivalent content and instruction semantics
- **AND** it SHALL not require the tool implementation to serialize a JSON result string for the SDK

#### Scenario: Failed tool result
- **WHEN** a tool returns a failed internal result
- **THEN** the protocol adapter SHALL emit the corresponding modern error/content response
- **AND** the client-visible error and embedded instructions SHALL be retained

### Requirement: Request-Scoped Tool Invocation
The tool registration layer SHALL provide each tool invocation with the application
request context and SHALL not require tool implementations to access a raw FastMCP
context or global active session.

The shared tool-argument contract SHALL include an optional FastMCP `session_id`.
The registration layer SHALL pass it to the request adapter when supplied, rather
than requiring individual tool implementations to resolve session ownership.

#### Scenario: A bound tool returns a new session ID
- **WHEN** `set_project(path)` or a stdio-PWD bootstrap creates and binds a FastMCP
  session
- **THEN** the common Result adapter SHALL include that `session_id` in the result's
  standard structured fixture
- **AND** it SHALL omit the fixture from results that neither create nor need to
  communicate a session ID

#### Scenario: Project-bound tool invocation
- **WHEN** a project-bound tool receives a request without valid project context
- **THEN** the registration layer SHALL return the no-project result before invoking the tool implementation
- **AND** it SHALL not create or persist a project from server process state, except
  for the defined one-time inherited-`PWD` bootstrap of an unbound stdio interaction

### Requirement: Path-Based Project Selection
The public `set_project` tool SHALL accept required `path`, an absolute client
filesystem project-root path, rather than a project `name`. It SHALL derive the root
identity from that path and bind only an unbound interaction. `switch_project(name)`
remains the independent active Guide configuration-project operation and SHALL not
change root binding. It SHALL resolve named configuration selection with the bound
root's hash, preserving same-named configurations at different roots.

#### Scenario: Agent selects its root
- **WHEN** an agent calls `set_project` with an absolute `path`
- **THEN** the tool SHALL bind the unbound interaction to the project identified by that path
- **AND** the agent-visible tool schema SHALL not offer a name-only selection argument

#### Scenario: Bound interaction calls set_project
- **WHEN** an interaction already has a bound root and calls `set_project` with any path
- **THEN** the tool SHALL reject the call without changing the root or active configuration selection

#### Scenario: Configuration switch uses the bound root identity
- **WHEN** a root-bound interaction calls `switch_project` with a configuration `name`
- **THEN** it SHALL resolve or create that configuration using the bound root hash
- **AND** it SHALL reject a filesystem path passed to `switch_project`
- **AND** it SHALL NOT select a same-named configuration with a missing or different hash

### Requirement: Current-Target Configuration Cloning
The public `clone_project` tool SHALL accept only source configuration
`from_project`, merge, and force arguments. `from_project` SHALL accept either a
display name or an exact hash-suffixed configuration key. The tool SHALL clone into
the active configuration project of the root-bound interaction and SHALL NOT accept
`to_project`, a target key, or a target path. The target write SHALL use the active
configuration's exact key and bound root hash.

For a source name without a hash suffix, lookup SHALL first use an exact raw
configuration key match, including a legacy hashless entry. This is an explicit
clone-only recovery path: it SHALL NOT make that entry selectable, listable, or
otherwise valid for ordinary project resolution. If no exact raw key exists, lookup
SHALL resolve a unique strictly valid hash-suffixed configuration with that display
name. An exact hash-suffixed source key SHALL be used directly and SHALL NOT fall
back to display-name resolution. If more than one strict hash-suffixed configuration
matches an unhashed source name, the tool SHALL report the ambiguity with the matching
keys and make no changes.

#### Scenario: Clone into current configuration
- **WHEN** a root-bound interaction calls `clone_project` with an exact source key or one unambiguous source configuration name
- **THEN** the tool SHALL copy configuration into that interaction's active configuration
- **AND** it SHALL NOT create, select, or modify any separately named target configuration

#### Scenario: Clone target is supplied
- **WHEN** a caller supplies a removed target-project argument to `clone_project`
- **THEN** the tool schema SHALL reject the request
- **AND** it SHALL not modify configuration

#### Scenario: Exact hashless recovery source
- **WHEN** `from_project` exactly matches a stored hashless configuration key
- **THEN** `clone_project` SHALL use it as a source only for that clone operation
- **AND** it SHALL write the copied configuration only to the root-bound target's
  valid hash-suffixed key
- **AND** it SHALL NOT make the hashless entry available to normal project selection

#### Scenario: Exact hash-suffixed source key
- **WHEN** `from_project` exactly matches a stored hash-suffixed configuration key
- **THEN** `clone_project` SHALL use that configuration as the source
- **AND** it SHALL not perform display-name ambiguity resolution

#### Scenario: Ambiguous source configuration name
- **WHEN** more than one stored configuration has the requested source name
- **THEN** `clone_project` SHALL report the ambiguity without modifying the current configuration
- **AND** it SHALL include the matching hash-suffixed configuration keys in the error
