## ADDED Requirements

### Requirement: Prompt Application Context Boundary
The prompt registration layer SHALL adapt raw FastMCP invocation data into a resolved
RequestContext before prompt routing and rendering. Prompt commands, help, content
lookups, and result processing SHALL use that same context throughout one invocation.

#### Scenario: Prompt routes to content or command handling
- **WHEN** a prompt invocation supplies a valid interaction identifier
- **THEN** every routed content or command operation SHALL use the Session and Project in its resolved RequestContext
- **AND** the prompt SHALL NOT perform a second session resolution without that interaction identity

