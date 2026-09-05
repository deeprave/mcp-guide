## ADDED Requirements

### Requirement: Tool Application Context Boundary
The tool registration layer SHALL adapt raw FastMCP invocation data into a resolved
RequestContext before invoking Guide tool application code. Internal tool
implementations and delegated tool helpers SHALL use that context rather than raw
FastMCP context.

#### Scenario: Tool delegates to another application helper
- **WHEN** a Guide tool delegates to content, project, category, collection, rendering,
  or task-result work
- **THEN** the delegated work SHALL receive the same resolved RequestContext
- **AND** it SHALL operate on the same Session and Project as the public tool invocation

