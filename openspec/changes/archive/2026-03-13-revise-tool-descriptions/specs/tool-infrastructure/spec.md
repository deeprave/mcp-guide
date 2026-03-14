## MODIFIED Requirements

### Requirement: Tool Description Standard for AI Agents
The system SHALL provide a standardized format for tool descriptions that enables AI agents to correctly understand and invoke tools without trial-and-error.

#### Scenario: Concise description structure
- **WHEN** a tool is documented
- **THEN** the docstring on the registered tool function contains a concise description (2-4 sentences)
- **AND** the description covers what the tool does and when to use it
- **AND** hand-written JSON Schema sections are NOT included in the docstring (redundant with auto-generated Arguments)
- **AND** Usage Instructions and Concrete Examples sections are NOT included (verbose, not MCP best practice)

#### Scenario: Auto-generated arguments section
- **WHEN** a tool is registered via `@toolfunc`
- **THEN** `build_description` appends a `## Arguments` block generated from Pydantic field descriptions
- **AND** this is the single source of parameter documentation for agents
- **AND** the combined description (concise docstring + auto-generated Arguments) is registered with FastMCP

#### Scenario: Template availability
- **WHEN** developer creates new tool
- **THEN** `src/mcp_guide/tools/README.md` provides the concise description standard
- **AND** template shows correct docstring placement on the registered function (not `internal_*`)
- **AND** template includes example of Pydantic Field descriptions that generate the Arguments section

#### Scenario: Docstring placement
- **WHEN** a tool has an `internal_*` implementation function
- **THEN** the agent-facing docstring is on the registered `@toolfunc` function
- **AND** the `internal_*` function may have a minimal or no docstring

#### Scenario: Complete field descriptions
- **WHEN** tool argument model is defined with Pydantic
- **THEN** every field includes `Field(description="...")` parameter
- **AND** description explains field purpose and valid values
- **AND** generated `## Arguments` block includes all field descriptions
